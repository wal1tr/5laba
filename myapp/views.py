import os
import xml.etree.ElementTree as ET
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from .forms import RecipeForm
from .models import Recipe
from django.core.files.storage import default_storage


import os
import xml.etree.ElementTree as ET
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import default_storage
from .forms import RecipeForm
from .models import Recipe


def recipe_form(request):
    """Форма добавления рецепта."""
    if request.method == "POST":
        form = RecipeForm(request.POST)
        if form.is_valid():
            # Получаем выбор сохранения
            save_choice = form.cleaned_data.get('save_choice')

            if save_choice == 'db':  # Сохранение в БД
                name = form.cleaned_data['name']
                if Recipe.objects.filter(name=name).exists():
                    form.add_error('name', 'Рецепт с таким названием уже существует.')
                else:
                    form.save()
                    return redirect('myapp:recipe_list')
            elif save_choice == 'xml':  # Сохранение в XML
                recipe = form.save(commit=False)
                recipe_xml = ET.Element("recipe")
                ET.SubElement(recipe_xml, "name").text = recipe.name
                ET.SubElement(recipe_xml, "ingredients").text = recipe.ingredients
                ET.SubElement(recipe_xml, "description").text = recipe.description

                # Убедимся, что директория существует
                recipes_dir = os.path.join(settings.MEDIA_ROOT, 'recipes')
                os.makedirs(recipes_dir, exist_ok=True)

                # Сохраняем XML файл
                file_path = os.path.join(recipes_dir, f"{recipe.name}.xml")
                ET.ElementTree(recipe_xml).write(file_path)

                return redirect('myapp:recipe_list')

    else:
        form = RecipeForm()

    return render(request, 'myapp/recipe_form.html', {'form': form})


import os
import xml.etree.ElementTree as ET
from django.shortcuts import render
from django.conf import settings
from .models import Recipe

from django.shortcuts import render
from .models import Recipe
import os
import xml.etree.ElementTree as ET
from django.conf import settings

def recipe_list(request):
    source = request.GET.get('source', '')  # Получаем параметр из URL (например, 'db' или 'xml')

    # Список всех рецептов из базы данных
    recipes_from_db = Recipe.objects.all()  # Получаем все рецепты из базы данных

    # Список всех XML файлов из директории
    recipes_dir = os.path.join(settings.MEDIA_ROOT, 'recipes')
    if not os.path.exists(recipes_dir):
        os.makedirs(recipes_dir)

    recipes_from_xml = []  # Список для хранения рецептов из XML файлов
    seen_names = set()  # Множество для хранения уникальных имен рецептов

    files = [f for f in os.listdir(recipes_dir) if f.endswith('.xml')]

    for file_name in files:
        file_path = os.path.join(recipes_dir, file_name)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Извлекаем данные рецепта из XML
            recipe = {
                'name': root.find('name').text,
                'ingredients': root.find('ingredients').text,
                'description': root.find('description').text,
                'source': 'xml',  # Источник: XML
                'pk': None  # Отсутствует pk
            }

            # Добавляем рецепт в список, если имя уникально
            if recipe['name'] not in seen_names:
                seen_names.add(recipe['name'])
                recipes_from_xml.append(recipe)

        except ET.ParseError:
            continue  # Игнорируем файлы, которые не могут быть распознаны как XML

    # Фильтруем рецепты в зависимости от выбранного источника
    if source == 'db':
        recipes = recipes_from_db
    elif source == 'xml':
        recipes = recipes_from_xml
    else:
        # Если источник не выбран, показываем все рецепты
        recipes = list(recipes_from_db) + recipes_from_xml

    return render(request, 'myapp/recipe_list.html', {'recipes': recipes, 'source': source})

def upload_file(request):
    """Обработка загрузки XML файла с рецептами."""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        
        # Убедимся, что директория для хранения файлов существует
        recipes_dir = os.path.join(settings.MEDIA_ROOT, 'recipes')
        os.makedirs(recipes_dir, exist_ok=True)

        # Полный путь для сохранения файла
        file_path = os.path.join(recipes_dir, file.name)
        
        # Сохраняем файл
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Проверяем расширение файла
        if not file.name.endswith('.xml'):
            return HttpResponse("Файл не является XML. Загрузите файл с расширением .xml.")

        # Проверяем валидность XML
        try:
            tree = ET.parse(file_path)
        except ET.ParseError:
            os.remove(file_path)  # Удаляем невалидный файл
            return HttpResponse("Файл невалидный. Пожалуйста, загрузите корректный XML файл.")

        # Парсим рецепты из XML
        root = tree.getroot()
        for recipe_element in root.findall('recipe'):
            name = recipe_element.find('name').text
            ingredients = recipe_element.find('ingredients').text
            description = recipe_element.find('description').text

            # Проверка на дубликаты перед добавлением в базу данных
            if not Recipe.objects.filter(name=name).exists():
                Recipe.objects.create(name=name, ingredients=ingredients, description=description)

        return redirect('myapp:recipe_list')

    return render(request, 'myapp/upload_file.html')


def download_recipes_xml(request):
    """Скачать все рецепты (из БД и XML) в одном XML-документе."""
    # Создаём корневой элемент XML
    root = ET.Element("recipes")

    # Добавляем рецепты из базы данных
    for recipe in Recipe.objects.all():
        recipe_element = ET.SubElement(root, "recipe")
        ET.SubElement(recipe_element, "name").text = recipe.name
        ET.SubElement(recipe_element, "ingredients").text = recipe.ingredients
        ET.SubElement(recipe_element, "description").text = recipe.description

    # Добавляем рецепты из XML файлов
    recipes_dir = os.path.join(settings.MEDIA_ROOT, 'recipes')
    if os.path.exists(recipes_dir):
        files = [f for f in os.listdir(recipes_dir) if f.endswith('.xml')]
        for file_name in files:
            file_path = os.path.join(recipes_dir, file_name)
            try:
                tree = ET.parse(file_path)
                recipe = tree.getroot()
                root.append(recipe)  # Добавляем рецепт в общий XML
            except ET.ParseError:
                continue  # Игнорируем невалидные XML-файлы

    # Генерируем XML-ответ для скачивания
    response = HttpResponse(
        ET.tostring(root, encoding='utf-8', method='xml'),
        content_type='application/xml'
    )
    response['Content-Disposition'] = 'attachment; filename="all_recipes.xml"'
    return response


def edit_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)

    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()  # Сохраняем изменения
            return redirect('myapp:recipe_list')
    else:
        form = RecipeForm(instance=recipe)

    return render(request, 'myapp/recipe_form.html', {'form': form, 'recipe': recipe})


def delete_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    recipe.delete()  # Удаляем рецепт
    return redirect('myapp:recipe_list')


from django.http import JsonResponse
from django.shortcuts import render
from .models import Recipe

def ajax_search(request):
    query = request.GET.get('q', '')  # Получаем запрос из GET параметра
    if query:
        recipes = Recipe.objects.filter(name__icontains=query)  # Ищем рецепты по имени
    else:
        recipes = Recipe.objects.all()  # Если запрос пустой, возвращаем все рецепты

    # Формируем список рецептов для отправки в ответе
    results = [{'id': recipe.id, 'name': recipe.name, 'ingredients': recipe.ingredients, 'description': recipe.description} for recipe in recipes]
    return JsonResponse({'recipes': results})
