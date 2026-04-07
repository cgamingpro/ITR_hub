from jose import JWTError, jwt , ExpiredSignatureError
from datetime import datetime, timedelta
from models import models
from fastapi import HTTPException, status, Depends 
from fastapi.security import OAuth2PasswordBearer
import os

auth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



rail = os.getenv("ENV")
if rail is not None and rail == "RAILWAY":
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

else:
    import local_config
    SECRET_KEY = local_config.SECRET_KEY
    ALGORITHM = local_config.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = local_config.ACCESS_TOKEN_EXPIRE_MINUTES


def create_acess_token(data: dict):
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_acess_token(token: str , credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        token_data = models.tokenData(user_id=user_id)
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return token_data.user_id
    
    
def get_current_user(token: str = Depends(auth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials" ,
                                          headers=  { "WWW-Authenticate": "Bearer"})
    return verify_acess_token(token, credentials_exception)
    