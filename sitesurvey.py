import json

class SiteSurvey:
    def __init__(self, survey_json):
        # Инициализация модели опроса на основе JSON
        self.survey_json = survey_json
        self.current_page = 0
        self.data = {}

    def on_survey_complete(self):
        # Обработка завершения опроса
        print("Опрос завершен с результатами:", self.data)
        # Здесь можно добавить логику, например, сохранение результатов в базу данных

    def on_page_changed(self):
        # Обработка изменения страницы
        print("Текущая страница изменена на:", self.survey_json["pages"][self.current_page]["name"])

    def render_survey(self):
        # Рендеринг текущей страницы опроса
        page = self.survey_json["pages"][self.current_page]
        print(f"Страница: {page['name']}")
        for element in page["elements"]:
            if element["type"] == "text":
                self.data[element["name"]] = input(f"{element['title']}: ")

    def next_page(self):
        # Переход на следующую страницу
        if self.current_page < len(self.survey_json["pages"]) - 1:
            self.current_page += 1
            self.on_page_changed()
        else:
            self.on_survey_complete()

    def get_survey_data(self):
        # Получение данных опроса
        return self.data

    def set_survey_data(self, data):
        # Установка данных опроса
        self.data = data


# Пример использования
survey_json = {
    "pages": [
        {
            "name": "page1",
            "elements": [
                {
                    "type": "text",
                    "name": "question1",
                    "title": "Как вас зовут?"
                }
            ]
        },
        {
            "name": "page2",
            "elements": [
                {
                    "type": "text",
                    "name": "question2",
                    "title": "Сколько вам лет?"
                }
            ]
        }
    ]
}

site_survey = SiteSurvey(survey_json)
site_survey.render_survey()  # Рендеринг первой страницы
site_survey.next_page()      # Переход на следующую страницу
site_survey.render_survey()  # Рендеринг второй страницы
site_survey.next_page()      # Завершение опроса