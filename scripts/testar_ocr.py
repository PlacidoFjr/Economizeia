#!/usr/bin/env python3
"""
Script para testar o OCR do FinGuia.
Cria uma imagem de teste com texto e testa a extração.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.ocr_service import ocr_service
from PIL import Image, ImageDraw, ImageFont
import io

def criar_imagem_teste():
    """Cria uma imagem de teste com texto de boleto."""
    # Criar imagem branca
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Texto de exemplo (simulando um boleto)
    textos = [
        "BANCO DO BRASIL",
        "Boleto de Pagamento",
        "Beneficiário: Energia Elétrica S.A.",
        "CNPJ: 12.345.678/0001-90",
        "Valor: R$ 150,50",
        "Vencimento: 15/12/2024",
        "Código de Barras: 00190500954014481606906809350314337370000000150",
        "Nosso Número: 123456789",
        "Instruções:",
        "1. Pagar até a data de vencimento",
        "2. Não aceitar após o vencimento",
        "3. Em caso de dúvidas, contatar o beneficiário"
    ]
    
    # Desenhar texto (sem fonte específica, usar padrão)
    y = 50
    for texto in textos:
        draw.text((50, y), texto, fill='black')
        y += 40
    
    # Salvar em bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def testar_ocr():
    """Testa a extração de texto usando o OCR."""
    print("🔍 Testando OCR do FinGuia...")
    print("=" * 60)
    
    # Criar imagem de teste
    print("\n1️⃣ Criando imagem de teste...")
    image_bytes = criar_imagem_teste()
    print("   ✅ Imagem criada com sucesso!")
    
    # Testar extração de imagem
    print("\n2️⃣ Extraindo texto da imagem...")
    try:
        texto, confianca = ocr_service.extract_text_from_image(image_bytes)
        
        print(f"   ✅ Extração concluída!")
        print(f"   📊 Confiança: {confianca * 100:.2f}%")
        print(f"   📝 Texto extraído ({len(texto)} caracteres):")
        print("   " + "-" * 56)
        
        # Mostrar texto formatado
        linhas = texto.split('\n') if '\n' in texto else texto.split()
        for linha in linhas[:15]:  # Mostrar primeiras 15 linhas
            if linha.strip():
                print(f"   {linha[:70]}")
        
        if len(linhas) > 15:
            print(f"   ... ({len(linhas) - 15} linhas restantes)")
        
        print("   " + "-" * 56)
        
        # Verificar palavras-chave esperadas
        palavras_chave = ['energia', 'elétrica', '150', '15/12/2024', 'banco', 'brasil']
        encontradas = []
        texto_lower = texto.lower()
        
        for palavra in palavras_chave:
            if palavra in texto_lower:
                encontradas.append(palavra)
        
        print(f"\n3️⃣ Palavras-chave encontradas: {len(encontradas)}/{len(palavras_chave)}")
        if encontradas:
            print(f"   ✅ Encontradas: {', '.join(encontradas)}")
        if len(encontradas) < len(palavras_chave):
            faltantes = [p for p in palavras_chave if p not in encontradas]
            print(f"   ⚠️  Faltantes: {', '.join(faltantes)}")
        
        # Resultado final
        print("\n" + "=" * 60)
        if confianca > 0.5:
            print("✅ OCR funcionando! Confiança aceitável.")
        elif confianca > 0.3:
            print("⚠️  OCR funcionando, mas com baixa confiança.")
        else:
            print("❌ OCR com problemas. Confiança muito baixa.")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao extrair texto: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_ocr()
    sys.exit(0 if sucesso else 1)

