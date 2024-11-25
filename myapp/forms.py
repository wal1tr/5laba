from django import forms
from .models import Recipe

class RecipeForm(forms.ModelForm):
    SAVE_CHOICES = [
        ('db', 'Сохранить в базу данных'),
        ('xml', 'Сохранить в XML файл'),
    ]

    save_choice = forms.ChoiceField(
        choices=SAVE_CHOICES,
        widget=forms.RadioSelect,
        label="Куда сохранить?"
    )

    class Meta:
        model = Recipe
        fields = ['name', 'ingredients', 'description', 'save_choice']
