from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Sequence, Table, Date
from sqlalchemy.orm import relationship

from codex.db.settings import get_session


Base = declarative_base()

author_documents = Table('author_documents', Base.metadata,
                         Column('author_id', ForeignKey('author.id'), primary_key=True),
                         Column('document_id', ForeignKey('document.id'), primary_key=True))

document_categories = Table('document_categories', Base.metadata,
                            Column('document_id', ForeignKey('document.id'), primary_key=True),
                            Column('category_id', ForeignKey('category.id'), primary_key=True))

shelf_documents = Table('shelf_documents', Base.metadata,
                        Column('shelf_id', ForeignKey('shelf.id'), primary_key=True),
                        Column('document_id', ForeignKey('document.id'), primary_key=True))


class Shelf(Base):

    __tablename__ = 'shelf'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String())
    description = Column(String())

    documents = relationship('Document', back_populates='shelf')


class Document(Base):

    __tablename__ = 'document'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    title = Column(String())
    path = Column(String())

    authors = relationship('Author', secondary=author_documents, back_populates='documents')
    categories = relationship('Category', secondary=document_categories, back_populates='documents',
                              order_by='asc(Category.id)')
    shelf_id = Column(Integer, ForeignKey('shelf.id'))
    shelf = relationship('Shelf', back_populates='documents')


class Author(Base):

    __tablename__ = 'author'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    first_name = Column(String(250))
    last_name = Column(String(250))
    middle_name = Column(String(250))

    documents = relationship('Document', secondary=author_documents, back_populates='authors')

    def __str__(self):
        return '{}, {} {}'.format(self.last_name or '', self.first_name or '', self.middle_name or '')


class Category(Base):

    __tablename__ = 'category'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(250))

    documents = relationship('Document', secondary=document_categories, back_populates='categories')
    parent_id = Column(Integer, ForeignKey('category.id'))
    subcategories = relationship('Category')

    def __str__(self):
        return self.name

    def find_item(self, category):

        def recursive_find(cat, target):
            for item in cat.subcategories:
                if target == item:
                    return item
                else:
                    return recursive_find(item, target)
            return None

        if category == self:
            return self
        recursive_find(self, category)

    def get_ancestor_chain(self):

        ancestors = []
        session = get_session()

        def get_ancestor_chain_recursive(category):
            if category.parent_id is not None:
                parent = session.query(Category).get(category.parent_id)
                ancestors.append(parent)
                get_ancestor_chain_recursive(parent)

        get_ancestor_chain_recursive(self)

        return ancestors

    def get_descendants(self):

        descendants = []

        def get_descendants_recursive(category: Category):
            for subcategory in category.subcategories:
                descendants.append(subcategory.id)
                get_descendants_recursive(subcategory)

        return descendants