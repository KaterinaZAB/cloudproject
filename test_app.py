import pytest
from app import app
@pytest.fixture
def client():
   with app.test_client() as client:
     yield client
 
# тест для проверки главной страницы
def test_home_page(client):
   response = client.get('/')
   assert response.status_code == 200 # проверка, что код ответа 200 
   assert b'Hello' in response.data # проверка, что текст присутствует на странице
   
# тест для маршрута, возвращающего данные
def test_data_page(client):
   response = client.get('/data')
   assert response.status_code == 200
   assert b'This is some data!' in response.data # проверка наличия кэшированных данных

def test_cache(client):
    response1 = client.get('/data')
    response2 = client.get('/data')
    assert response1.data == response2.data  # данные должны быть одинаковыми из-за кэша

def test_404(client):
    response = client.get('/page404')
    assert response.status_code == 404
