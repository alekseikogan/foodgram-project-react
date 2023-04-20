from django.core import validators

MinValueValidator = validators.MinValueValidator
MaxValueValidator = validators.MaxValueValidator


class TagSlugValidator(validators.RegexValidator):
    '''Валидатор для тега'''
    regex = r'^[a-zA-Z]{1}[\w]+$'
    message = 'Тег должен состоять из букв и цифр!'


class HexColorValidator(validators.RegexValidator):
    '''Валидатор для цвета'''
    regex = r'^#([A-Fa-f0-9]{6})$'
    message = 'Ошибка в теге цвета!'
