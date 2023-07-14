import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt

import os
from datetime import timedelta

from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now


l = []
TOKEN = 't.yCJnMe2E7ksgzVWJNPfnVZLxunQOtCE_koKG6RCPYLkzJGzH1s26q_SnWhiU1r1rdnbEVZSElZK27nAw0mAZxg'
FIGI = 'BBG00475KKY8'

with Client(TOKEN) as client:
    for candle in client.get_all_candles(figi=FIGI, from_=now() - timedelta(days=60), interval=CandleInterval.CANDLE_INTERVAL_1_MIN):
        l.append({
            'close': candle.close
        })
candles_data = pd.DataFrame(l)
print(candles_data.iloc[0])
# Загрузка данных из файла или другого источника
# candles_data - массив свечей торгов
# candles_data должен содержать столбцы с открытием, закрытием, максимумом и минимумом цен
# Например: candles_data = pd.read_csv('data.csv')

# Предобработка данных
# Отберем только цены закрытия



data = candles_data['close'].apply(lambda x: x.units).values.reshape(-1, 1)

# Нормализация данных
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

# Разделение на обучающий и тестовый наборы данных
train_size = int(len(scaled_data) * 0.8)
test_size = len(scaled_data) - train_size
train_data, test_data = scaled_data[:train_size], scaled_data[train_size:]

# Генерация последовательностей для обучения
def generate_sequences(data, sequence_length):
    X = []
    y = []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i+sequence_length])
        y.append(data[i+sequence_length])
    return np.array(X), np.array(y)

sequence_length = 300  # Длина последовательности
X_train, y_train = generate_sequences(train_data, sequence_length)
X_test, y_test = generate_sequences(test_data, sequence_length)

# Создание модели LSTM
model = Sequential()
model.add(LSTM(units=80, input_shape=(sequence_length, 1)))
model.add(Dense(units=1))
model.compile(optimizer='adam', loss='mean_squared_error')

# Обучение модели
model.fit(X_train, y_train, epochs=10, batch_size=32)

# Предсказание на тестовых данных
predictions = model.predict(X_test)

# Обратное масштабирование предсказанных данных
predictions = scaler.inverse_transform(predictions)

# Визуализация предсказаний и исходных данных
plt.plot(scaler.inverse_transform(test_data[sequence_length:]), label='Исходные данные')
plt.plot(predictions, label='Предсказания')
plt.xlabel('Временной индекс')
plt.ylabel('Цена закрытия')
plt.legend()
plt.show()

# Оценка точности модели
mse = np.mean((predictions - scaler.inverse_transform(test_data[sequence_length:])) ** 2)
print('Средняя квадратичная ошибка (MSE):', mse)

model.save_weights('weights.h5')
