from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from pachong.zk import fetch_goods_by_creeper

# 初始化 FastAPI 应用
app = FastAPI()

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

class Product(Base):
    __tablename__ = "products"
    name = Column(String, primary_key=True, index=True)
    price = Column(Float)
    image = Column(String)
    from_ = Column(String)  # 表示商品来源
    link = Column(String)

# 创建数据库表
Base.metadata.create_all(bind=engine)
Product.__table__.create(bind=engine, checkfirst=True)

# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 创建数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 注册请求模型
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


@app.post("/register")
async def register(user: RegisterRequest, db: Session = Depends(get_db)):
    print("register main.py")
    # 检查用户是否已存在
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该电子邮件已被注册")

    # 创建新用户并保存到数据库
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "注册成功"}


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(user: LoginRequest, db: Session = Depends(get_db)):
    print("login main.py")
    # 检查用户是否存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="用户名或密码不正确")

    print("login success")
    return {"message": "登录成功"}


@app.get("/api/search")
async def search_products(query: str):
    print("search main.py ", query)
    try:
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
        # print("length",len(filter_goods))
        return filter_goods
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProductRequest(BaseModel):
    name: str
    price: float
    image: str
    from_: str
    link: str

@app.post("/api/favorites")
async def add_favorite(product: ProductRequest, db: Session = Depends(get_db)):
    print("main post api/favorites")
    # 检查商品是否已在收藏中
    existing_product = db.query(Product).filter(Product.name == product.name).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="商品已被收藏")

    # 添加商品到数据库
    new_product = Product(
        name=product.name,
        price=product.price,
        image=product.image,
        from_=product.from_,
        link=product.link
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {"message": "商品已成功收藏"}

@app.delete("/api/favorites")
async def remove_favorite(product: ProductRequest, db: Session = Depends(get_db)):
    # 删除商品
    print("main delete api/favorites")
    db_product = db.query(Product).filter(Product.name == product.name).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="商品未找到")

    db.delete(db_product)
    db.commit()

    return {"message": "商品已从收藏中移除"}


# 主入口
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
