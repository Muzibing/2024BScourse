import requests
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func  # 用于自动获取当前时间

from pachong.zk import fetch_goods_by_creeper
from pachong.suning import SuningProductSpider
from pachong.taobaoagain import get_taobao_price
from emailsender import send_email

# 初始化 FastAPI 应用
app = FastAPI()

global_if_login = False
global_username = ""

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境下应指定允许的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置数据库
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 定义用户模型
class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)


# 定义商品模型
class Product(Base):
    __tablename__ = "products"
    name = Column(String, primary_key=True, index=True)
    price = Column(Float)
    image = Column(String)
    from_ = Column(String)  # 表示商品来源
    link = Column(String)
    user_username = Column(String, ForeignKey("users.username"))  # 引用用户表中的用户名
    created_at = Column(DateTime, default=func.now())  # 自动设置当前时间

    # 外键关系
    user = relationship("User", backref="products")


# 创建数据库表
Base.metadata.create_all(bind=engine)

# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 创建数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 请求模型
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


@app.on_event("startup")
async def print_routes():
    for route in app.routes:
        print(route.path)


# 注册接口
@app.post("/register")
async def register(user: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该电子邮件已被注册")

    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "注册成功"}


# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str


# 登录接口
@app.post("/login")
async def login(user: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="用户名或密码不正确")

    global global_username, global_if_login
    global_if_login = True
    global_username = user.username
    return {"message": "登录成功"}


# 商品请求模型
class ProductRequest(BaseModel):
    name: str
    price: float
    image: str
    from_: str
    link: str


@app.get("/api/search")
async def search_products(query: str):
    try:
        # print("before")
        # spider = SuningProductSpider(query)
        # print("middle")
        # all_goods2 = spider.get_comment_data()
        # print(type(all_goods2))
        # print("after")
        all_goods = fetch_goods_by_creeper(query)
        filter_goods = [
            {
                "name": item["title"],
                "price": item["price"],
                "image": item["image_url"],
                "from": item["from"],
                "link": item["jump_url"]
            }
            for item in all_goods
        ]
        # return filter_goods + all_goods2
        return filter_goods
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 收藏商品接口
@app.post("/api/favorites")
async def add_favorite(
        product: ProductRequest,
        db: Session = Depends(get_db)
):
    # 检查用户是否已登录
    username = global_username
    if not global_if_login:
        raise HTTPException(status_code=401, detail="未登录，无法收藏商品")

    # 检查商品是否已在收藏中
    existing_product = db.query(Product).filter(Product.name == product.name, Product.user_username == username).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="商品已被收藏")

    # 获取用户对象，确保用户名存在
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # 添加商品到数据库，并关联用户名
    new_product = Product(
        name=product.name,
        price=product.price,
        image=product.image,
        from_=product.from_,
        link=product.link,
        user_username=username  # 记录当前用户的用户名
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {"message": "商品已成功收藏"}


# 获取收藏商品接口
@app.get("/api/favorites")
async def get_favorites(db: Session = Depends(get_db)):
    try:
        # 获取所有收藏商品
        favorites = db.query(Product).all()
        return [
            {
                "name": fav.name,
                "price": fav.price,
                "image": fav.image,
                "from": fav.from_,
                "link": fav.link,
                "user_username": fav.user_username,  # 返回用户名
                "created_at": fav.created_at  # 返回商品添加的时间
            }
            for fav in favorites if global_username == fav.user_username
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checkpricedrop")
async def check_price_drop(
        product: ProductRequest,
        db: Session = Depends(get_db)
):
    try:
        link = product.link
        if product.from_ == 'UlandTaoBao':
            # price = get_taobao_price(link)
            price_new = product.price - 1
            if price_new < product.price:
                print(product.name, " 降价")
                product = db.query(Product).filter(Product.name == product.name).first()
                product.price = price_new
                product.created_at = func.now()
                db.commit()
                db.refresh(product)
                print("数据库已经更新")
                to_email = db.query(User.email).filter(User.username == global_username).first()
                to_email2 = str(to_email[0])
                # 千万别用f'"{to_email[0]}"'，虽然也是string类型，但就是会报500错
                # print("查到接收邮箱了", to_email2, "3348536459@qq.com", type(to_email2))
                # print("3348536459@qq.com" == to_email2)
                send_email(to_email2, "降价", "降价为")
                print("邮件发完了")
                return {"isDiscounted": True, "message": "降价"}
            else:
                return {"isDiscounted": False, "message": "未降价"}
        else:
            return {"isDiscounted": False, "message": "来源不对"}


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 主入口
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
