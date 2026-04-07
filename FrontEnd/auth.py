from jose import JWTError, jwt , ExpiredSignatureError
from datetime import datetime, timedelta
from models import models
from fastapi import HTTPException, status, Depends 
from fastapi.security import OAuth2PasswordBearer


auth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "weoiqruyweoiruyqewiorqywieryoqwieuryqio"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
    