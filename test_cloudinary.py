import cloudinary
import cloudinary.uploader
import os
from PIL import Image
import io

print("Iniciando teste do Cloudinary...")

# Configuração do Cloudinary
print("Configurando Cloudinary...")
cloudinary.config(
    cloud_name="dkj83qihx",
    api_key="695527639461583",
    api_secret="p5MJmNhADIqnLm7z5GPzbesRNeM"
)

def test_cloudinary_upload():
    try:
        print("Criando imagem de teste...")
        # Criar uma imagem de teste
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        print("Iniciando upload para o Cloudinary...")
        # Upload para o Cloudinary
        result = cloudinary.uploader.upload(
            img_byte_arr,
            folder="test",
            public_id="test_image",
            resource_type="auto"
        )
        
        print("Upload realizado com sucesso!")
        print("URL da imagem:", result.get('secure_url'))
        print("Resposta completa do Cloudinary:", result)
        return True
    except Exception as e:
        print(f"Erro ao fazer upload: {e}")
        return False

if __name__ == "__main__":
    print("Executando teste...")
    test_cloudinary_upload()
    print("Teste finalizado.") 