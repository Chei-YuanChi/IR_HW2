from django.db import models
import ast

class ListField(models.TextField):

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return str(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

# Create your models here.
class File_data(models.Model):
    Title_index = models.IntegerField(default = 0)
    Title = models.TextField(default = "")
    Context = models.TextField(default = "")
    Sentences_num = models.IntegerField(default = 0)
    Words_num = models.IntegerField(default = 0)
    Chars_num = models.IntegerField(default = 0)

class Word_index(models.Model):
    Word = models.TextField(default = "")
    Index = ListField()

class Word_num(models.Model):
    Word = models.TextField(default = "")
    Counts = models.IntegerField(default = 0)

class Word_nosw_num(models.Model):
    Word = models.TextField(default = "")
    Counts = models.IntegerField(default = 0)

class Word_stem_num(models.Model):
    Word = models.TextField(default = "")
    Counts = models.IntegerField(default = 0)

class IDF(models.Model):
    Word = models.TextField(default = "")
    Artical_num = models.IntegerField(default = 0)

class Artical_word_num(models.Model):
    Artical_index = models.IntegerField(default = 0)
    Counts = models.IntegerField(default = 0)

class Artical_word_num_nosw(models.Model):
    Artical_index = models.IntegerField(default = 0)
    Counts = models.IntegerField(default = 0)

class Word_Artical(models.Model):
    Word = models.TextField(default = "")
    Artical_index = models.IntegerField(default = 0)
    Counts = models.IntegerField(default = 0)

class Word_Artical_nosw(models.Model):
    Word = models.TextField(default = "")
    Artical_index = models.IntegerField(default = 0)
    Counts = models.IntegerField(default = 0)