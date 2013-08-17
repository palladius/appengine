"""
Yet another attempt to get a good sql store.
"""
from base64 import b64encode, b64decode
from sqlalchemy import select, desc
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relation, mapper, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import Table, Column, PrimaryKeyConstraint,\
    ForeignKeyConstraint, Index, MetaData
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import Unicode, Integer, String, UnicodeText, CHAR
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import Policy
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.model.tiddler import Tiddler, string_to_tags_list
from tiddlyweb.model.user import User
from tiddlyweb.serializer import Serializer
from tiddlyweb.store import NoBagError, NoRecipeError, NoTiddlerError, \
    NoUserError
from tiddlyweb.stores import StorageInterface

#import logging
#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

metadata = MetaData()
Session = sessionmaker()

field_table = Table('field', metadata,
    Column('bag_name', Unicode(128), nullable=False),
    Column('tiddler_title', Unicode(128), nullable=False),
    Column('revision_number', Integer, nullable=False),
    Column('name', Unicode(128), nullable=False),
    Column('value', Unicode(1024)),
    PrimaryKeyConstraint('bag_name', 'tiddler_title', 'revision_number',
        'name'),
    ForeignKeyConstraint(['bag_name', 'tiddler_title', 'revision_number'],
                         ['revision.bag_name', 'revision.tiddler_title',
                             'revision.number'],
                         onupdate='CASCADE', ondelete='CASCADE'),
    )

revision_table = Table('revision', metadata,
    Column('bag_name', Unicode(128), nullable=False),
    Column('tiddler_title', Unicode(128), nullable=False),
    Column('number', Integer, nullable=False),
    Column('modifier', Unicode(128)),
    Column('modified', String(14)),
    Column('type', String(128)),
    Column('tags', Unicode(1024)),
    Column('text', UnicodeText, nullable=False, default=u''),
    PrimaryKeyConstraint('bag_name', 'tiddler_title', 'number'),
    ForeignKeyConstraint(['bag_name', 'tiddler_title'],
                         ['tiddler.bag_name', 'tiddler.title'],
                         onupdate='CASCADE', ondelete='CASCADE'),
    )

tiddler_table = Table('tiddler', metadata,
    Column('bag_name', Unicode(128), nullable=False),
    Column('title', Unicode(128), nullable=False),
    PrimaryKeyConstraint('bag_name', 'title'),
    ForeignKeyConstraint(['bag_name'], ['bag.name'],
        onupdate='CASCADE', ondelete='CASCADE'),
    )

bag_table = Table('bag', metadata,
    Column('name', Unicode(128), primary_key=True),
    Column('desc', Unicode(1024)),
    )

policy_table = Table('policy', metadata,
    Column('container_name', Unicode(128), nullable=False),
    Column('type', String(12), nullable=False),
    Column('principal_name', Unicode(128), nullable=False),
    Column('principal_type', CHAR(1), nullable=False),
    PrimaryKeyConstraint('container_name', 'type'),
    ForeignKeyConstraint(['principal_name', 'principal_type'],
        ['principal.name', 'principal.type'],
        onupdate='CASCADE', ondelete='CASCADE'),
    )

Index('policy_idx', policy_table.c.principal_name)

recipe_table = Table('recipe', metadata,
    Column('name', Unicode(128), primary_key=True, nullable=False),
    Column('desc', Unicode(1024)),
    Column('recipe_string', UnicodeText, default=u''),
    )

principal_table = Table('principal', metadata,
    Column('name', Unicode(128), nullable=False),
    Column('type', CHAR(1), nullable=False),
    PrimaryKeyConstraint('name', 'type'),
    )

role_table = Table('role', metadata,
    Column('user', Unicode(128), nullable=False),
    Column('name', Unicode(50), nullable=False),
    PrimaryKeyConstraint('user','name'),
    ForeignKeyConstraint(['user'], ['user.usersign'],
        onupdate='CASCADE', ondelete='CASCADE'),
    )

user_table = Table('user', metadata,
    Column('usersign', Unicode(128), primary_key=True, nullable=False),
    Column('note', Unicode(1024)),
    Column('password', String(128)),
    PrimaryKeyConstraint('usersign'),
    )


class sField(object):

    def __repr__(self):
        return '<sField(%s:%s:%d:%s)>' % (self.bag_name,
                self.tiddler_title, self.revision_number, self.name)


class sRevision(object):

    def __init__(self):
        object.__init__(self)
        self.number = 1

    def __repr__(self):
        return '<sRevision(%s:%s:%d)>' % (self.bag_name,
                self.tiddler_title, self.number)


class sTiddler(object):

    def __init__(self, title, bag_name, rev=None):
        object.__init__(self)
        self.title = title
        self.bag_name = bag_name
        self.rev = rev

    def revision(self):
        """
        Calculate the current revision of this tiddler.
        """
        if hasattr(self, 'rev') and self.rev:
            return self.revisions[self.rev - 1]
        return self.revisions[-1]

    def created(self):
        """
        Calculate the created field for this tiddler from
        the first revision.
        """
        return self.revisions[0].modified

    def creator(self):
        """
        Calculate the creator field for this tiddler from
        the first revision.
        """
        return self.revisions[0].modifier

    def __repr__(self):
        return '<sTiddler(%s:%s)>' % (self.bag_name, self.title)


class sPolicy(object):

    def __repr__(self):
        return '<sPolicy(%s:%s:%s:%s)>' % (self.container_name,
                self.principal_type, self.principal_name, self.type)


class sBag(object):

    def __init__(self, name, desc=''):
        object.__init__(self)
        self.name = name
        self.desc = desc

    def __repr__(self):
        return '<sBag(%s)>' % (self.name)


class sRecipe(object):

    def __init__(self, name, desc=''):
        self.name = name
        self.desc = desc

    def __repr__(self):
        return '<sRecipe(%s)>' % (self.name)


class sPrincipal(object):

    def __repr__(self):
        return '<sPrincipal(%s:%s)>' % (self.type, self.name)


class sRole(object):

    def __repr__(self):
        return '<sRole(%s:%s)>' % (self.user, self.name)


class sUser(object):

    def __repr__(self):
        return '<sUser(%s)>' % (self.usersign)


mapper(sField, field_table)

mapper(sRevision, revision_table, properties=dict(
    fields=relation(sField,
        backref='revision',
        cascade='delete',
        lazy=False)))

mapper(sTiddler, tiddler_table, properties=dict(
    revisions=relation(sRevision,
        backref='tiddler',
        order_by=sRevision.number,
        cascade='delete',
        lazy=False)))

mapper(sBag, bag_table, properties=dict(
    tiddlers=relation(sTiddler,
        backref='bag',
        cascade='delete'),
    policy=relation(sPolicy,
        primaryjoin=(policy_table.c.container_name==bag_table.c.name),
        cascade='delete',
        foreign_keys=policy_table.c.container_name,
        lazy=False)))

mapper(sUser, user_table, properties=dict(
    roles=relation(sRole,
        lazy=False,
        cascade='delete')))

mapper(sPolicy, policy_table)

mapper(sRecipe, recipe_table, properties=dict(
    policy=relation(sPolicy,
        primaryjoin=(policy_table.c.container_name==recipe_table.c.name),
        cascade='delete',
        foreign_keys=policy_table.c.container_name,
        lazy=False)))

mapper(sRole, role_table)

mapper(sPrincipal, principal_table)


class Store(StorageInterface):
    """
    A SqlAlchemy based storage interface for TiddlyWeb.
    """

    session = None

    def __init__(self, store_config=None, environ=None):
        super(Store, self).__init__(store_config, environ)
        self._init_store()

    def _init_store(self):
        """
        Establish the database engine and session,
        creating tables if needed.
        """
        store_type = self._db_config().split(':', 1)[0]
        if store_type == 'sqlite' or not Store.session:
            engine = create_engine(self._db_config(), pool_recycle=True)
            metadata.create_all(engine)
            Session.configure(bind=engine)
            Store.session = Session()
        self.session = Store.session
        self.serializer = Serializer('text')

    def _db_config(self):
        return self.store_config['db_config']

    def list_recipes(self):
        return (self._load_recipe(Recipe(srecipe.name), srecipe)
                for srecipe in self.session.query(sRecipe).all())

    def list_bags(self):
        return (self._load_bag(Bag(sbag.name), sbag)
                for sbag in self.session.query(sBag).all())

    def list_users(self):
        return (self._load_user(User(suser.usersign), suser)
                for suser in self.session.query(sUser).all())

    def list_tiddler_revisions(self, tiddler):
        revisions = [row[0] for row in
                select([revision_table.c.number],
                    whereclause=and_(
                        revision_table.c.tiddler_title==tiddler.title,
                        revision_table.c.bag_name==tiddler.bag),
                    order_by=desc(revision_table.c.number),
                    bind=self.session.get_bind(None)).execute()]
        if not revisions:
            raise NoTiddlerError('tiddler %s not found' % (tiddler.title,))
        else:
            return revisions

    def recipe_delete(self, recipe):
        try:
            try:
                srecipe = self.session.query(sRecipe).filter(sRecipe.name==recipe.name).one()
                self.session.delete(srecipe)
                self.session.commit()
            except NoResultFound, exc:
                raise NoRecipeError('no results for recipe %s, %s' % (recipe.name, exc))
        except:
            self.session.rollback()
            raise

    def recipe_get(self, recipe):
        try:
            srecipe = self.session.query(sRecipe).filter(sRecipe.name==recipe.name).one()
            recipe = self._load_recipe(recipe, srecipe)
            return recipe
        except NoResultFound, exc:
            raise NoRecipeError('no results for recipe %s, %s' % (recipe.name, exc))

    def recipe_put(self, recipe):
        try:
            srecipe = self._store_recipe(recipe)
            self.session.merge(srecipe)
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def bag_delete(self, bag):
        try:
            try:
                sbag = self.session.query(sBag).filter(sBag.name==bag.name).one()
                self.session.delete(sbag)
                self.session.commit()
            except NoResultFound, exc:
                raise NoBagError('Bag %s not found: %s' % (bag.name, exc))
        except:
            self.session.rollback()
            raise

    def bag_get(self, bag):
        try:
            sbag = self.session.query(sBag).filter(sBag.name == bag.name).one()
            bag = self._load_bag(bag, sbag)

            try:
                store = self.environ['tiddlyweb.store']
            except KeyError:
                store = False

            if not (hasattr(bag, 'skinny') and bag.skinny):

                def _bags_tiddler(stiddler):
                    tiddler = Tiddler(stiddler.title)
                    tiddler = self._load_tiddler(tiddler, stiddler)
                    tiddler.store = store
                    return tiddler

                stiddlers = sbag.tiddlers
                bag.add_tiddlers(_bags_tiddler(stiddler)
                        for stiddler in stiddlers)
            return bag
        except NoResultFound, exc:
            raise NoBagError('Bag %s not found: %s' % (bag.name, exc))

    def bag_put(self, bag):
        try:
            sbag = self._store_bag(bag)
            self.session.merge(sbag)
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def tiddler_delete(self, tiddler):
        try:
            try:
                stiddler = (self.session.query(sTiddler).
                        filter(sTiddler.title==tiddler.title).
                        filter(sTiddler.bag_name==tiddler.bag).one())
                self.session.delete(stiddler)
                self.session.commit()
                self.tiddler_written(tiddler)
            except NoResultFound, exc:
                raise NoTiddlerError('no tiddler %s to delete, %s' % (tiddler.title, exc))
        except:
            self.session.rollback()
            raise

    def tiddler_get(self, tiddler):
        try:
            stiddler = (self.session.query(sTiddler).
                    filter(sTiddler.title==tiddler.title).
                    filter(sTiddler.bag_name==tiddler.bag).one())
            tiddler = self._load_tiddler(tiddler, stiddler)
            return tiddler
        except NoResultFound, exc:
            raise NoTiddlerError('Tiddler %s not found: %s' % (tiddler.title, exc))

    def tiddler_put(self, tiddler):
        try:
            if not tiddler.bag:
                raise NoBagError('bag required to save')
            stiddler = self._store_tiddler(tiddler)
            self.session.merge(stiddler)
            self.session.commit()
            self.tiddler_written(tiddler)
        except:
            self.session.rollback()
            raise

    def user_delete(self, user):
        try:
            try:
                suser = self.session.query(sUser).filter(sUser.usersign==user.usersign).one()
                self.session.delete(suser)
                self.session.commit()
            except NoResultFound, exc:
                raise NoUserError('user %s not found, %s' % (user.usersign, exc))
        except:
            self.session.rollback()

    def user_get(self, user):
        try:
            suser = self.session.query(sUser).filter(sUser.usersign==user.usersign).one()
            user = self._load_user(user, suser)
            return user
        except NoResultFound, exc:
            raise NoUserError('user %s not found, %s' % (user.usersign, exc))

    def user_put(self, user):
        try:
            suser = self._store_user(user)
            self.session.merge(suser)
            self._store_roles(user)
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def _load_bag(self, bag, sbag):
        bag.desc = sbag.desc
        bag.policy = self._load_policy(sbag.policy)
        bag.store = True
        return bag

    def _load_policy(self, spolicy):
        policy = Policy()

        if spolicy is not None:
            for pol in spolicy:
                principal_name = pol.principal_name
                if pol.principal_type == 'R':
                    principal_name = 'R:%s' % pol.principal_name
                if pol.type == 'owner':
                    policy.owner = principal_name
                else:
                    principals = getattr(policy, pol.type, [])
                    principals.append(principal_name)
                    setattr(policy, pol.type, principals)
        return policy

    def _load_tiddler(self, tiddler, stiddler):
        try:
            if tiddler.revision:
                stiddler.rev = tiddler.revision
            revision = stiddler.revision()

            tiddler.modifier = revision.modifier
            tiddler.modified = revision.modified
            tiddler.revision = revision.number
            tiddler.type = revision.type

            if tiddler.type and tiddler.type != 'None' and not tiddler.type.startswith('text/'):
                tiddler.text = b64decode(revision.text.lstrip().rstrip())
            else:
                tiddler.text = revision.text
            tiddler.tags = self._load_tags(revision.tags)

            for sfield in revision.fields:
                tiddler.fields[sfield.name] = sfield.value

            tiddler.created = stiddler.created()
            tiddler.creator = stiddler.creator()

            return tiddler
        except IndexError, exc:
            raise NoTiddlerError('No revision %s for tiddler %s, %s' %
                    (stiddler.rev, stiddler.title, exc))

    def _load_recipe(self, recipe, srecipe):
        recipe.desc = srecipe.desc
        recipe.policy = self._load_policy(srecipe.policy)
        recipe.set_recipe(self._load_recipe_string(srecipe.recipe_string))
        recipe.store = True
        return recipe

    def _load_recipe_string(self, recipe_string):
        recipe = []
        if recipe_string:
            for line in recipe_string.split('\n'):
                bag, filter = line.split('?', 1)
                recipe.append((bag, filter))
        return recipe

    def _load_tags(self, tags_string):
        return string_to_tags_list(tags_string)

    def _load_user(self, user, suser):
        user.usersign = suser.usersign
        user._password = suser.password
        user.note = suser.note
        [user.add_role(role.name) for role in suser.roles]
        return user

    def _store_bag(self, bag):
        sbag = sBag(bag.name, bag.desc)
        self._store_policy(bag.name, bag.policy)
        return sbag

    def _store_policy(self, container, policy):
        for attribute in policy.attributes:

            if attribute == 'owner':
                policy.owner = policy.owner is None and [] or [policy.owner]
            for principal_name in getattr(policy, attribute, []):
                if principal_name is not None:
                    spolicy = sPolicy()
                    spolicy.container_name = container
                    spolicy.type = attribute

                    if principal_name.startswith('R:'):
                        pname = principal_name[2:]
                        ptype = 'R'
                    else:
                        pname = principal_name
                        ptype = 'U'

                    try:
                        sprincipal=(self.session.query(sPrincipal).
                                    filter(sPrincipal.name==pname).
                                    filter(sPrincipal.type==ptype).one())
                    except NoResultFound:
                        sprincipal = sPrincipal()
                        sprincipal.name = pname
                        sprincipal.type = ptype
                        self.session.add(sprincipal)
                        self.session.flush()

                    spolicy.principal_name = sprincipal.name
                    spolicy.principal_type = sprincipal.type
                    self.session.merge(spolicy)

    def _store_recipe(self, recipe):
        srecipe = sRecipe(recipe.name, recipe.desc)
        self._store_policy(recipe.name, recipe.policy)
        srecipe.recipe_string = self._store_recipe_string(recipe)
        return srecipe

    def _store_recipe_string(self, recipe_list):
        string = u''
        string += u'\n'.join([u'%s?%s' % (unicode(bag),
            unicode(filter_string)) for bag, filter_string in recipe_list])
        return string

    def _store_roles(self, user):
        usersign = user.usersign
        for role in user.roles:
            srole = sRole()
            srole.user = usersign
            srole.name = role
            self.session.merge(srole)

    def _store_tags(self, tags):
        return self.serializer.serialization.tags_as(tags)

    def _store_tiddler(self, tiddler):
        if self._tiddler_exists(tiddler.title, tiddler.bag):
            stiddler = (self.session.query(sTiddler).
                    filter(sTiddler.title == tiddler.title).
                    filter(sTiddler.bag_name == tiddler.bag).one())
        else:
            stiddler = sTiddler(tiddler.title, tiddler.bag)
            self.session.add(stiddler)

        if tiddler.type and tiddler.type != 'None' and not tiddler.type.startswith('text/'):
            tiddler.text = unicode(b64encode(tiddler.text))

        srevision = sRevision()
        srevision.bag_name = stiddler.bag_name
        srevision.tiddler_title = stiddler.title
        srevision.type = tiddler.type
        srevision.modified = tiddler.modified
        srevision.modifier = tiddler.modifier
        srevision.text = tiddler.text
        srevision.tags = self._store_tags(tiddler.tags)
        try:
            srevision.number = stiddler.revisions[-1].number + 1
        except IndexError:
            srevision.number = 1

        self.session.add(srevision)

        for field in tiddler.fields:
            if field.startswith('server.'):
                continue
            sfield = sField()
            sfield.bag_name = stiddler.bag_name
            sfield.tiddler_title = stiddler.title
            sfield.revision_number = srevision.number
            sfield.name = field
            sfield.value = tiddler.fields[field]
            self.session.add(sfield)

        # we need to update the revision on the tiddlyweb tiddler
        # so the correct ETag is set.
        tiddler.revision = srevision.number
        return stiddler

    def _store_user(self, user):
        suser = sUser()
        suser.usersign = user.usersign
        suser.password = user._password
        suser.note = user.note
        return suser

    def _tiddler_exists(self, tiddler_title, bag_name):
        rows = tiddler_table.select(
                and_(tiddler_table.c.title==tiddler_title,
                    tiddler_table.c.bag_name==bag_name),
                bind=self.session.get_bind(None)).execute().fetchone()
        return rows is not None
