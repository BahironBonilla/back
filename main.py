from mimetypes import MimeTypes
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
import psycopg2
import boto3
from botocore.exceptions import NoCredentialsError


app = FastAPI()

AWS_ACCESS_KEY_ID = 'AKIA2HHT3BBJKEJ7HL4J'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = 'us-east-2'  # Reemplaza con tu región
S3_BUCKET_NAME = 'canasto'

# Configura tus credenciales de base de datos
DATABASE_CONFIG = {
    "host": "database-1.cwmd0ueayfgt.us-east-2.rds.amazonaws.com",
    "user": "postgres",
    "password": "postgres",
    "database": "postgres",
    "port": 5432,
}

# Inicializa una conexión a la base de datos al inicio de la aplicación
db_connection = psycopg2.connect(**DATABASE_CONFIG)

# Función de dependencia para obtener la conexión a la base de datos
def get_db():
    # Devuelve la conexión que ya está abierta
    return db_connection

# Ruta protegida que usa la conexión a la base de datos
@app.get("/protected")
async def protected_route(db: psycopg2.extensions.connection = Depends(get_db)):
    # Puedes realizar operaciones en la base de datos aquí
    # En este ejemplo, simplemente devolvemos un mensaje
    return {"message": "Operaciones en la base de datos exitosas"}

# Ruta de ejemplo sin conexión a la base de datos
@app.get("/")
async def read_root():
    return {"message": "¡Hola, FastAPI!"}

# Ruta para crear una tabla en la base de datos
@app.post("/create_table")
async def create_table(db: psycopg2.extensions.connection = Depends(get_db)):
    # Ejemplo: Crear una tabla llamada "ejemplo" con una columna "id"
    query = '''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    identification_number VARCHAR(20) NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    lastname VARCHAR(50) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    phone VARCHAR(10) NOT NULL,
                    address VARCHAR(70) NOT NULL,
                    password VARCHAR(20) NOT NULL profile_picture BYTEA
                );
                    CREATE TABLE IF NOT EXISTS metodos_pago (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
                    type VARCHAR(50) NOT NULL,
                    number VARCHAR(15) NOT NULL
                );
                    CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
                    product VARCHAR(50) NOT NULL,
                    description VARCHAR(150) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    stock INT NOT NULL
                );
                    CREATE TABLE IF NOT EXISTS qr_codes (
                    id SERIAL PRIMARY KEY,
                    metodos_pago_id INT REFERENCES metodos_pago(id) ON DELETE CASCADE,
                    url VARCHAR(255) NOT NULL
                );
                    CREATE TABLE IF NOT EXISTS profile_pictures (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
                    url VARCHAR(255) NOT NULL
                );

            '''
    with db.cursor() as cursor:
        cursor.execute(query)
    db.commit()
    return {"message": "Tabla creada exitosamente"}




s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)


# Ruta para insertar un nuevo usuario
@app.post("/insert_user")
async def insert_user(user_data: dict, db: psycopg2.extensions.connection = Depends(get_db)):
         
    query = '''
        INSERT INTO usuarios (identification_number, name, lastname, email, phone, address, password)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    '''
    with db.cursor() as cursor:
        cursor.execute(query, (
            user_data["identification_number"],
            user_data["name"],
            user_data["lastname"],
            user_data["email"],
            user_data["phone"],
            user_data["address"],
            user_data["password"]
        ))
    db.commit()
    return {"message": "Usuario insertado exitosamente"}

# Ruta para insertar un nuevo método de pago
@app.post("/insert_payment_method")
async def insert_payment_method(payment_data: dict, db: psycopg2.extensions.connection = Depends(get_db)):
    query = '''
        INSERT INTO public.metodos_pago(id, user_id, type, number)
	    VALUES (%s,%s,%s,%s);
    '''
    with db.cursor() as cursor:
        cursor.execute(query, (
            payment_data["id"],
            payment_data["user_id"],
            payment_data["type"],
            payment_data["number"]
        ))
    db.commit()
    return {"message": "Método de pago insertado exitosamente"}

# Ruta para insertar un nuevo producto
@app.post("/insert_product")
async def insert_product(product_data: dict, db: psycopg2.extensions.connection = Depends(get_db)):
    query = '''
        INSERT INTO public.productos(id, user_id, product, description, price, stock)
	    VALUES (%s, %s, %s, %s, %s, %s);
    '''
    with db.cursor() as cursor:
        cursor.execute(query, (
            product_data["id"],
            product_data["user_id"],
            product_data["product"],
            product_data["description"],
            product_data["price"],
            product_data["stock"]
        ))
    db.commit()
    return {"message": "Producto insertado exitosamente"}
#
## Ruta para actualizar las tablas
#@app.post("/update_tables")
#async def update_tables(db: psycopg2.extensions.connection = Depends(get_db)):
#    try:
#        # Agrega el atributo 'profile_picture' a la tabla 'usuarios' si no existe
#        with db.cursor() as cursor:
#            cursor.execute("ALTER TABLE IF EXISTS usuarios ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(300);")
#
#        # Agrega el atributo 'qr' a la tabla 'metodos_pago' si no existe
#        with db.cursor() as cursor:
#            cursor.execute("ALTER TABLE IF EXISTS metodos_pago ADD COLUMN IF NOT EXISTS qr VARCHAR(300);")
#
#        # Realiza la confirmación para aplicar los cambios
#        db.commit()
#
#        return {"message": "Tablas actualizadas exitosamente"}
#
#    except Exception as e:
#        # Si hay algún error, lanza una excepción HTTP
#        raise HTTPException(status_code=500, detail=f"Error al actualizar las tablas: {str(e)}")
#    
# Ruta para obtener todos los usuarios
@app.get("/get_all_users")
async def get_all_users(db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        # Realiza la consulta a la tabla 'usuarios'
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios;")
            users = cursor.fetchall()

        # Formatea el resultado como una lista de diccionarios
        users_list = []
        for user in users:
            user_dict = {
                "id": user[0],
                "identification_number": user[1],
                "name": user[2],
                "lastname": user[3],
                "email": user[4],
                "phone": user[5],
                "address": user[6],
                # Puedes incluir más campos según tu estructura de datos
            }
            users_list.append(user_dict)

        return {"users": users_list}

    except Exception as e:
        # Si hay algún error, lanza una excepción HTTP
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")
    
# Ruta para obtener los métodos de pago de un usuario
@app.get("/get_payment_methods/{user_id}")
async def get_payment_methods(user_id: int, db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        # Realiza la consulta a la tabla 'metodos_pago' para un usuario específico
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM metodos_pago WHERE user_id = %s;", (user_id,))
            payment_methods = cursor.fetchall()

        # Formatea el resultado como una lista de diccionarios
        payment_methods_list = []
        for method in payment_methods:
            method_dict = {
                "id": method[0],
                "user_id": method[1],
                "type": method[2],
                "number": method[3],
                # Puedes incluir más campos según tu estructura de datos
            }
            payment_methods_list.append(method_dict)

        return {"payment_methods": payment_methods_list}

    except Exception as e:
        # Si hay algún error, lanza una excepción HTTP
        raise HTTPException(status_code=500, detail=f"Error al obtener métodos de pago: {str(e)}")
    
# Ruta para obtener los productos de un usuario
@app.get("/get_user_products/{user_id}")
async def get_user_products(user_id: int, db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        # Realiza la consulta a la tabla 'productos' para un usuario específico
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM productos WHERE user_id = %s;", (user_id,))
            user_products = cursor.fetchall()

        # Formatea el resultado como una lista de diccionarios
        user_products_list = []
        for product in user_products:
            product_dict = {
                "id": product[0],
                "user_id": product[1],
                "product": product[2],
                "description": product[3],
                "price": float(product[4]),  # Convierte a float para manejar el tipo DECIMAL
                "stock": product[5],
                # Puedes incluir más campos según tu estructura de datos
            }
            user_products_list.append(product_dict)

        return {"user_products": user_products_list}

    except Exception as e:
        # Si hay algún error, lanza una excepción HTTP
        raise HTTPException(status_code=500, detail=f"Error al obtener productos: {str(e)}")
    

#Ruta para subir una imagen a S3 de profile_picture
@app.post("/upload_to_s4_profile_picture")
async def upload_to_s3(file: UploadFile = File(...), user_id: int = Form(...), db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        # Verifica el tipo MIME del archivo
        mime = MimeTypes()
        content_type, _ = mime.guess_type(file.filename)

        # Asegúrate de que el tipo MIME sea 'image/*'
        if content_type and content_type.startswith('image/'):
            # Configura los encabezados para que el archivo se muestre en lugar de descargarse
            extra_args = {'ContentType': content_type, 'ContentDisposition': 'inline'}

            # Sube el archivo al bucket de S3 con los encabezados configurados
            s3.upload_fileobj(file.file, S3_BUCKET_NAME, file.filename, ExtraArgs=extra_args)

            # URL del archivo en S3
            s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file.filename}"

            # Inserta la URL en la tabla 'profile_pictures'
            query_insert_profile_picture = '''
                INSERT INTO profile_pictures (user_id, url)
                VALUES (%s, %s);
            '''
            with db.cursor() as cursor:
                cursor.execute(query_insert_profile_picture, (user_id, s3_url))
            db.commit()

            return {"message": "Imagen subida exitosamente a S3", "s3_url": s3_url}
        else:
            raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Credenciales de AWS no válidas o ausentes")
    except Exception as e:
        # Imprime el error para obtener más detalles
        print(f"Error al subir la imagen a S3: {str(e)}")
        # Lanza una excepción HTTP
        raise HTTPException(status_code=500, detail="Error al subir la imagen a S3. Consulta los registros para obtener más detalles.")

# Ruta para subir un código QR a S3
@app.post("/upload_to_s3_qr_code")
async def upload_to_s3_qr_code(file: UploadFile = File(...), payment_method_id: int = Form(...), db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        # Verifica el tipo MIME del archivo
        mime = MimeTypes()
        content_type, _ = mime.guess_type(file.filename)

        # Asegúrate de que el tipo MIME sea 'image/*'
        if content_type and content_type.startswith('image/'):
            # Configura los encabezados para que el archivo se muestre en lugar de descargarse
            extra_args = {'ContentType': content_type, 'ContentDisposition': 'inline'}

            # Sube el archivo al bucket de S3 con los encabezados configurados
            s3.upload_fileobj(file.file, S3_BUCKET_NAME, file.filename, ExtraArgs=extra_args)

            # URL del archivo en S3
            s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file.filename}"

            # Inserta la URL en la tabla 'qr_codes'
            query_insert_qr_code = '''
                INSERT INTO qr_codes (metodos_pago_id, url)
                VALUES (%s, %s);
            '''
            with db.cursor() as cursor:
                cursor.execute(query_insert_qr_code, (payment_method_id, s3_url))
            db.commit()

            return {"message": "Código QR subido exitosamente a S3", "s3_url": s3_url}
        else:
            raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Credenciales de AWS no válidas o ausentes")
    except Exception as e:
        # Imprime el error para obtener más detalles
        print(f"Error al subir el código QR a S3: {str(e)}")
        # Lanza una excepción HTTP
        raise HTTPException(status_code=500, detail="Error al subir el código QR a S3. Consulta los registros para obtener más detalles.")







# Ruta para subir una imagen a S3
@app.post("/upload_to_s3")
async def upload_to_s3(file: UploadFile = File(...), user_id: int = Form(...), db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        # Verifica el tipo MIME del archivo
        mime = MimeTypes()
        content_type, _ = mime.guess_type(file.filename)

        # Asegúrate de que el tipo MIME sea 'image/*'
        if content_type and content_type.startswith('image/'):
            # Configura los encabezados para que el archivo se muestre en lugar de descargarse
            extra_args = {'ContentType': content_type, 'ContentDisposition': 'inline'}

            # Sube el archivo al bucket de S3 con los encabezados configurados
            s3.upload_fileobj(file.file, S3_BUCKET_NAME, file.filename, ExtraArgs=extra_args)

            # URL del archivo en S3
            s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file.filename}"

            # Inserta la URL en la tabla 'profile_pictures'
            query_insert_profile_picture = '''
                INSERT INTO profile_pictures (user_id, url)
                VALUES (%s, %s);
            '''
            with db.cursor() as cursor:
                cursor.execute(query_insert_profile_picture, (user_id, s3_url))
            db.commit()

            return {"message": "Imagen subida exitosamente a S3", "s3_url": s3_url}
        else:
            raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Credenciales de AWS no válidas o ausentes")
    except Exception as e:
        # Si hay algún otro error, lanza una excepción HTTP
        raise HTTPException(status_code=500, detail=f"Error al subir la imagen a S3: {str(e)}")


s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
# Ruta para mostrar una imagen desde S3
@app.get("/get_image/{image_key}")
async def get_image(image_key: str):
    try:
        # Genera una URL prefirmada con una duración de 60 segundos
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': image_key},
            ExpiresIn=60
        )

        # Retorna la URL prefirmada como respuesta
        return {"presigned_url": presigned_url}

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Credenciales de AWS no válidas o ausentes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar la URL prefirmada: {str(e)}")

# Obtén el número de puerto en el que se ejecuta la aplicación
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

