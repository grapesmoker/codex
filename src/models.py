from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Sequence, Table, Date
from sqlalchemy.orm import relationship

Base = declarative_base()


author_documents = Table('author_documents', Base.metadata,
                         Column('author_id', ForeignKey('authors.id'), primary_key=True),
                         Column('document_id', ForeignKey('documents.id'), primary_key=True))

document_categories = Table('document_categories', Base.metadata,
                            Column('document_id', ForeignKey('documents.id'), primary_key=True),
                            Column('category_id', ForeignKey('categories.id'), primary_key=True))

library_documents = Table('library_documents', Base.metadata,
                          Column('library_id', ForeignKey('libraries.id'), primary_key=True),
                          Column('document_id', ForeignKey('documents.id'), primary_key=True))

library_authors = Table('library_authors', Base.metadata,
                        Column('library_id', ForeignKey('libraries.id'), primary_key=True),
                        Column('author_id', ForeignKey('authors.id'), primary_key=True))

library_categories = Table('library_categories', Base.metadata,
                        Column('library_id', ForeignKey('libraries.id'), primary_key=True),
                        Column('category_id', ForeignKey('categories.id'), primary_key=True))


class Library(Base):
    
    __tablename__ = 'libraries'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(500))
    
    documents = relationship('Document', back_populates='library')
    authors = relationship('Author', back_populates='library')
    categories = relationship('Category', back_populates='library')


class Document(Base):

    __tablename__ = 'documents'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    title = Column(String(500))
    path = Column(String(1000))

    authors = relationship('Author', secondary=author_documents, back_populates='documents')
    categories = relationship('Category', secondary=document_categories, back_populates='documents',
                              order_by='asc(Category.id)')
    library_id = Column(Integer, ForeignKey('libraries.id'))
    library = relationship('Library', back_populates='documents')


class Author(Base):

    __tablename__ = 'authors'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    first_name = Column(String(250))
    last_name = Column(String(250))
    middle_name = Column(String(250))
    library_id = Column(Integer, ForeignKey('libraries.id'))
    
    documents = relationship('Document', secondary=author_documents, back_populates='authors')
    library = relationship('Library', back_populates='authors')

    def __str__(self):
        # return '<Author id={}, first_name={}, last_name={}>'.format(self.id, self.first_name, self.last_name)
        return '{}, {} {}'.format(self.last_name or '', self.first_name or '', self.middle_name or '')


class Category(Base):

    __tablename__ = 'categories'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(250))

    documents = relationship('Document', secondary=document_categories, back_populates='categories')
    library_id = Column(Integer, ForeignKey('libraries.id'))
    library = relationship('Library', back_populates='categories')
    parent_id = Column(Integer, ForeignKey('categories.id'))
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