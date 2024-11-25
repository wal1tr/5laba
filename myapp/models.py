from django.db import models

class Recipe(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Уникальное имя для проверки дубликатов
    ingredients = models.TextField()  # Ингредиенты
    description = models.TextField()  # Описание
    created_at = models.DateTimeField(auto_now_add=True)  # Дата добавления
    updated_at = models.DateTimeField(auto_now=True)  # Дата последнего обновления

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
