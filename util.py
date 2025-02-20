from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import os
import configparser


def write_config(app):
    app.config.set('Settings', 'window_width', str(app.config.getint('Settings', 'window_width', fallback = 1000)))
    app.config.set('Settings', 'window_height', str(app.config.getint('Settings', 'window_height', fallback = 600)))
    app.config.set('Settings', 'grid_col', str(app.config.getint('Settings', 'grid_col', fallback = 3)))
    app.config.set('Settings', 'grid_row', str(app.config.getint('Settings', 'grid_row', fallback = 2)))
    with open('config.ini', 'w') as configfile:
        app.config.write(configfile)


def read_config(app):
    app.config = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        app.config.read('config.ini')
    else:
        app.config['Settings'] = {}
        write_config(app)
        read_config(app)
    app.window_width = app.config.getint('Settings', 'window_width', fallback = 1000)
    app.window_height = app.config.getint('Settings', 'window_height', fallback = 600)
    app.grid_col = app.config.getint('Settings', 'grid_col', fallback = 3)
    app.grid_row = app.config.getint('Settings', 'grid_row', fallback = 2)


def formatting_data(resetmethod, resettime, resetparam0, resetparam1):
    method_dict = {'일간': 0, '주간': 1, '월간': 2, '주기': 3}
    resetmethod = method_dict[resetmethod]
    weekday_dict = {'월요일': 0, '화요일': 1, '수요일': 2, '목요일': 3, '금요일': 4, '토요일': 5, '일요일': 6}

    if resetmethod == 0:
        split_timestr = resettime.split(':')
        resettime = int(split_timestr[0]) * 60 + int(split_timestr[1])  # ex) 05:00(%H:%M) -> 300(Minute)
        resetparam0 = -1 # 사용안함
        resetparam1 = -1

    elif resetmethod == 1:
        split_timestr = resettime.split(':')
        resettime = int(split_timestr[0]) * 60 + int(split_timestr[1])  # ex) 05:00(%H:%M) -> 300(Minute)
        resetparam0 = weekday_dict[resetparam0] # 요일
        resetparam1 = -1

    elif resetmethod == 2:
        split_timestr = resettime.split(':')
        resettime = int(split_timestr[0]) * 60 + int(split_timestr[1])  # ex) 05:00(%H:%M) -> 300(Minute)
        resetparam0 = resetparam0[:-1] # 일
        resetparam1 = -1

    elif resetmethod == 3: 
        resettime = -1
        resetparam0 = resetparam0 # 초기화 주기
        resetparam1 = resetparam1 # 기준 날짜

    return resetmethod, resettime, resetparam0, resetparam1


def reset_check(checked, lastchecktime, resetmethod, resettime, resetparam0, resetparam1):
    # 체크가 되어있는 경우
    if checked:
        # 체크박스 초기화 알고리즘 실행
        # 0: daily, 1: weekly, 2: monthly, 3: cycle
        if resetmethod == 0: checked = daily_reset(resettime, lastchecktime)
        if resetmethod == 1: checked = weekly_reset(resettime, lastchecktime, resetparam0)
        if resetmethod == 2: checked = monthly_reset(resettime, lastchecktime, resetparam0)
        if resetmethod == 3: checked, resetparam1 = cycle_reset(resetparam0, resetparam1)
    else:
        if resetmethod == 3: checked, resetparam1 = cycle_reset(resetparam0, resetparam1)
        checked = 0
    return checked, resetparam1


# json 구성
# ['row', 'col', 'name', 'checked', 'lastchecktime', 'reset', 'reset_time_input', 'resetparam0', 'resetparam1']
def load_data(app):
    # json에서 유저 일정 데이터 읽기
    file_path = 'userdata.json'
    if os.path.exists(file_path):
        df = pd.read_json(file_path, orient='records', lines=True)

        # 일정 갯수에 따라 반복문 실행
        for i in range(len(df)):
            row = df.iloc[i, 0]
            col = df.iloc[i, 1]
            todoname = df.iloc[i, 2]
            checked = df.iloc[i, 3]
            lastchecktime = df.iloc[i, 4]
            resetmethod = df.iloc[i, 5]
            resettime = df.iloc[i, 6]
            resetparam0 = df.iloc[i, 7]
            resetparam1 = df.iloc[i, 8]

            checked, resetparam1 = reset_check(checked, lastchecktime, resetmethod, resettime, resetparam0, resetparam1)

            app.show_todo(row, col, todoname, lastchecktime, resetmethod, resettime, resetparam0, resetparam1, checked)
            

def save_data(app):
    write_config(app)
    start_time = datetime.now()

    file_path = 'userdata.json'
    data = []
    lastchecktime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for row in range(app.grid_row):
        for col in range(app.grid_col):
            todo_list = app.todo_list[f'list{row * 3 + col}']
            for i in range(todo_list.count()):
                item = todo_list.item(i)
                widget = todo_list.itemWidget(item)

                todoname = item.data(0)
                box_checked = widget.layout().itemAt(widget.layout().count() - 2).widget().isChecked() # 메소드에 따라 아이템 갯수가 유동적이니 뒤에서부터 세는 방식으로 구현
                box_checked = 1 if box_checked else 0
                resetmethod = widget.layout().itemAt(0).widget().text()
                resettime = widget.layout().itemAt(1).widget().text()
                resetparam0 = widget.layout().itemAt(2).widget().text()
                resetparam1 = widget.layout().itemAt(3).widget().text()

                resetmethod, resettime, resetparam0, resetparam1 = formatting_data(resetmethod, resettime, resetparam0, resetparam1)

                checked, resetparam1 = reset_check(box_checked, app.lastchecktime, resetmethod, resettime, resetparam0, resetparam1)
                if checked != box_checked or resetmethod == 3: todo_list.update_param(item, resetmethod, resettime, resetparam0, resetparam1, checked)

                data.append([row, col, todoname, checked, lastchecktime, resetmethod, resettime, resetparam0, resetparam1])
    
    app.lastchecktime = lastchecktime

    df = pd.DataFrame(data, columns=['row', 'col', 'name', 'checked', 'lastchecktime', 'reset', 'reset_time_input', 'resetparam0', 'resetparam1'])
    df.to_json(file_path, orient='records', lines=True)

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    print(f'[{end_time.hour:02d}:{end_time.minute:02d}] 저장 완료, 소요 시간: {elapsed_time.total_seconds():.6f}s')


#     1. 시간별(daily), 요일별(weekly), 매 달 ~일 등(monthly)
#         현재 시간 기준으로 초기화 주기에 따른 지난번 초기화 시간을 계산하고, 마지막 체크 시간이 지난번 초기화 시간 이전이라면 체크 해제

#         패러미터 구성
#             daily - 시간 (분) + 마지막 체크 시간, 2개
#             weekly - 요일 + 시간 + 마지막 체크 시간, 3개
#             monthly - 일자 + 시간 + 마지막 체크 시간, 3개


# reset_time_input : 분 단위(0-1439), lastchecktime : %Y-%m-%d %H:%M:%S ex)2025-01-27 11:30:21
def daily_reset(reset_time_input, lastchecktime): 
    now = datetime.now()
    reset_time = time(reset_time_input // 60, reset_time_input % 60, 0)

    # 현재 시간과 초기화 시간을 비교하여 지난번 초기화 시간 계산
    if now.time() < reset_time: 
        pre_reset_time = datetime.combine(now.date() - timedelta(days = 1), reset_time)
    else:
        pre_reset_time = datetime.combine(now.date(), reset_time)

    # 마지막 체크 시간이 지난번 초기화 시간 이전인지 확인
    # 지난번 초기화 시간 이후후면 체크 해제(0), 지난번 초기화 시간 이전이면 체크 유지(1)
    lastcheck = datetime.strptime(lastchecktime, '%Y-%m-%d %H:%M:%S')
    if lastcheck < pre_reset_time: 
        return 0
    else:
        return 1


# reset_time_input : 분 단위(0-1439), lastchecktime : %Y-%m-%d %H:%M:%S ex)2025-01-27 11:30:21, resetparam0 : 요일(0-6)
def weekly_reset(reset_time_input, lastchecktime, resetparam0):
    now = datetime.now()
    reset_time = time(reset_time_input // 60, reset_time_input % 60, 0)
    weekday = int(resetparam0)

    # 선택한 요일에서 현재 요일까지의 차이 계산
    days_since_weekday = now.weekday() - weekday
    
    # 다른 요일
    if days_since_weekday > 0: 
        pre_reset_time = datetime.combine(now.date() - timedelta(days = days_since_weekday), reset_time)
    elif days_since_weekday < 0: 
        pre_reset_time = datetime.combine(now.date() - timedelta(days = 7 - days_since_weekday), reset_time)
    # 같은 요일
    else:
        if now.time() < reset_time: 
            pre_reset_time = datetime.combine(now.date() - timedelta(days = 7), reset_time)
        else:
            pre_reset_time = datetime.combine(now.date(), reset_time)

    lastcheck = datetime.strptime(lastchecktime, '%Y-%m-%d %H:%M:%S')
    if lastcheck < pre_reset_time: 
        return 0
    else:
        return 1


# reset_time_input : 분 단위(0-1439), lastchecktime : %Y-%m-%d %H:%M:%S ex)2025-01-27 11:30:21, resetparam0 : 일자(1-31)
def monthly_reset(reset_time_input, lastchecktime, resetparam0):
    now = datetime.now()
    reset_time = time(reset_time_input // 60, reset_time_input % 60, 0)
    reset_day= int(resetparam0)

    if now.day < reset_day: # 이번달 초기화 일자를 지나지 않은 경우
        pre_reset_time = datetime.combine((now.date() - relativedelta(months = 1)).replace(day = reset_day), reset_time)
    elif now.day == reset_day: # 초기화 당일
        if now.time() < reset_time: 
            pre_reset_time = datetime.combine(now.date() - relativedelta(months = 1), reset_time)
        else:
            pre_reset_time = datetime.combine(now.date(), reset_time)
    else: # 이번달 초기화 일자를 지난 경우
        pre_reset_time = datetime.combine(now.date().replace(day = reset_day), reset_time)

    lastcheck = datetime.strptime(lastchecktime, '%Y-%m-%d %H:%M:%S')
    if lastcheck < pre_reset_time: 
        return 0
    else:
        return 1


#     2. 주기별(기준 시간 정하고, 그 시간 기준으로 주기 설정, 초기화시 기준 시간 변경)
#         1. 현재 시간이 기준 시간과 초기화 시간 사이라면 유지.
#         2. 아니라면 초기화 하고 기준 시간을 초기화 시간으로 변경
#         3. 변경된 기준 시간으로 새로운 초기화 시간을 계산하고, 1번으로

#         패러미터 구성     
#           초기화 주기, 기준 날짜 2개

# resetparam0 : 분 단위, resetparam1: %Y-%m-%d %H:%M:%S ex)2025-01-27 11:30:21
def cycle_reset(resetparam0, resetparam1):
    now = datetime.now()
    reset_cycle = int(resetparam0)
    base_datetime = datetime.strptime(resetparam1, '%Y-%m-%d %H:%M:%S')

    next_reset_time = base_datetime + timedelta(minutes = reset_cycle)

    if base_datetime < now < next_reset_time:
        return 1, base_datetime.strftime('%Y-%m-%d %H:%M:%S')
    else:
        while next_reset_time < now:
            base_datetime += timedelta(minutes = reset_cycle)
            next_reset_time = base_datetime + timedelta(minutes = reset_cycle)
        return 0, base_datetime.strftime('%Y-%m-%d %H:%M:%S')