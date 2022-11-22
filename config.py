db = {
    # 데이터베이스에 접속할 사용자 아이디
    'user': 'root',
    # 사용자 비밀번호
    'password': 'imsohappy',
    # 접속할 데이터베이스의 주소 (같은 컴퓨터에 있는 데이터베이스에 접속하기 때문에 localhost)
    'host': 'jupiterdb.cbll7n774vcb.ap-northeast-2.rds.amazonaws.com',
    # 관계형 데이터베이스는 주로 3306 포트를 통해 연결됨
    'port': 3306,
    # 실제 사용할 데이터베이스 이름
    'database': 'test2db'
}
db_url = f"mysql+pymysql://{db['user']}:{db['password']}@" \
         f"{db['host']}:{db['port']}/{db['database']}?charset=utf8"