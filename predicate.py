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
FIGI = 'BBG000MZL2S9'

with Client(TOKEN) as client:
    for candle in client.get_all_candles(figi=FIGI, from_=now() - timedelta(days=180), interval=CandleInterval.CANDLE_INTERVAL_15_MIN):
        l.append({
            'close': candle.close
        })
candles_data = pd.DataFrame(l)
print(candles_data.iloc[0])

# Загрузка данных
data = candles_data['close'].apply(lambda x: x.units).values.reshape(-1, 1)

# Предобработка данных
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(data)

# Создание последовательностей временных рядов
X = []
y = []
n = len(scaled_data)
sequence_length = 200  # Число свечей в последовательности
future_steps = 5  # Число свечей в будущем, для которых нужно предсказать направление движения цены

for i in range(sequence_length, n - future_steps):
    X.append(scaled_data[i-sequence_length:i, 0])
    y.append(scaled_data[i+future_steps, 0])

X = np.array(X)
y = np.array(y)

# Разделение данных на обучающий и тестовый наборы
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1, shuffle=False)

# Создание модели LSTM
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(sequence_length, 1)))
model.add(LSTM(units=50))
model.add(Dense(units=1, activation='sigmoid'))

# Компиляция модели
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Обучение модели или загрузка предварительно обученных весов
train_model = True
weights_file = 'model_weights.h5'

if train_model:
    # Обучение модели
    model.fit(X_train, y_train, epochs=10, batch_size=32)

    # Сохранение весов модели
    model.save_weights(weights_file)
else:
    # Загрузка весов модели
    model.load_weights(weights_file)

# Оценка модели на тестовых данных
loss, accuracy = model.evaluate(X_test, y_test)
print("Accuracy:", accuracy)
# Предсказание направления движения цены на будущие свечи

future_data = scaled_data[-sequence_length:].reshape(1, -1, 1)
predicted_direction = model.predict(future_data)
print(predicted_direction)


predicted_price = scaler.inverse_transform(predicted_direction.reshape(-1, 1))[0][0]


print("Predicted Price:", predicted_price)


plt.plot(scaler.inverse_transform(future_data.reshape(-1, 1)), label='Предсказания')

plt.xlabel('Future Steps')
plt.ylabel('Price')
plt.title('Predicted Price Movement')
plt.legend()
plt.show()
