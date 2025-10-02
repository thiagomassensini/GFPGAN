import gradio as gr
import subprocess
import uuid
import tempfile
from pathlib import Path
from PIL import Image


def validate_image(image):
    """Valida se a imagem é válida e pode ser processada."""
    try:
        if image is None:
            return False, "Nenhuma imagem fornecida"
        # Verifica se a imagem pode ser aberta
        if hasattr(image, 'size'):
            return True, "OK"
        return False, "Formato de imagem inválido"
    except Exception as e:
        return False, f"Erro ao validar imagem: {str(e)}"


def enhance_face(input_image, version="1.3", upscale=2):
    """
    Restaura e aprimora rostos usando GFPGAN.

    Args:
        input_image: Imagem PIL de entrada
        version: Versão do modelo GFPGAN (1.2, 1.3, 1.4)
        upscale: Fator de escala (1, 2, 3, 4)

    Returns:
        Caminho para a imagem restaurada ou None em caso de erro
    """
    # Validação de entrada
    is_valid, message = validate_image(input_image)
    if not is_valid:
        print(f"[GFPGAN] Erro de validação: {message}")
        gr.Warning(message)
        return None

    # Criar diretório temporário
    temp_dir = Path(tempfile.mkdtemp(prefix="gfpgan_"))
    unique_id = str(uuid.uuid4())[:8]
    input_path = temp_dir / f"input_{unique_id}.png"
    output_dir = temp_dir / "output"

    try:
        # Salvar imagem de entrada
        input_image.save(input_path)
        print(f"[GFPGAN] Imagem salva em: {input_path}")

        # Preparar comando
        command = [
            "python", "inference_gfpgan.py",
            "-i", str(input_path),
            "-o", str(output_dir),
            "-v", str(version),
            "-s", str(upscale)
        ]

        print(f"[GFPGAN] Executando: {' '.join(command)}")

        # Executar GFPGAN com timeout
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )

        # Log do resultado
        if result.stdout:
            print(f"[GFPGAN] STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"[GFPGAN] STDERR:\n{result.stderr}")

        # Verificar código de retorno
        if result.returncode != 0:
            error_msg = f"Erro no processamento (código {result.returncode})"
            if result.stderr:
                error_msg += f": {result.stderr[:200]}"
            print(f"[GFPGAN] {error_msg}")
            gr.Warning(error_msg)
            return None

        # Procurar arquivo de saída
        restored_dir = output_dir / "restored_imgs"
        if not restored_dir.exists():
            print(f"[GFPGAN] Diretório de saída não encontrado: {restored_dir}")
            gr.Warning("Diretório de saída não foi criado")
            return None

        # Buscar primeira imagem restaurada
        output_files = list(restored_dir.glob("*.png"))
        if not output_files:
            print(f"[GFPGAN] Nenhuma imagem restaurada encontrada em {restored_dir}")
            gr.Warning("Nenhuma imagem restaurada foi gerada")
            return None

        output_path = output_files[0]
        print(f"[GFPGAN] Imagem restaurada encontrada: {output_path}")

        # Validar imagem de saída
        try:
            with Image.open(output_path) as img:
                img.load()  # Força carregar a imagem para validar
            print("[GFPGAN] Imagem restaurada validada com sucesso")
            return str(output_path)
        except Exception as img_err:
            print(f"[GFPGAN] Erro ao validar imagem de saída: {img_err}")
            gr.Warning("Imagem de saída corrompida")
            return None

    except subprocess.TimeoutExpired:
        print("[GFPGAN] Timeout ao processar imagem")
        gr.Warning("Processamento excedeu tempo limite (5 minutos)")
        return None
    except Exception as e:
        print(f"[GFPGAN] Erro inesperado: {e}")
        gr.Warning(f"Erro ao processar: {str(e)[:100]}")
        return None
    finally:
        # Limpar arquivos temporários após um delay (para permitir que Gradio carregue a imagem)
        # Nota: Em produção, considere usar um sistema de limpeza agendada
        pass  # temp_dir será mantido para que Gradio possa servir a imagem


# Criar interface
with gr.Blocks(title="GFPGAN - Restauração Facial") as demo:
    gr.Markdown("""
    # 🎨 GFPGAN - Restauração Facial com IA

    Faça upload de uma foto de rosto para restaurar e aprimorar usando GFPGAN.
    O modelo funciona melhor com fotos de rostos humanos, mesmo de baixa qualidade.
    """)

    with gr.Row():
        with gr.Column():
            input_img = gr.Image(type="pil", label="📤 Imagem Original")
            with gr.Row():
                version_select = gr.Dropdown(
                    choices=["1.2", "1.3", "1.4"],
                    value="1.3",
                    label="Versão do Modelo",
                    info="1.3 é recomendado para uso geral"
                )
                upscale_select = gr.Slider(
                    minimum=1,
                    maximum=4,
                    step=1,
                    value=2,
                    label="Fator de Escala",
                    info="Aumenta a resolução da imagem"
                )
            process_btn = gr.Button("✨ Restaurar Rosto", variant="primary")

        with gr.Column():
            output_img = gr.Image(type="filepath", label="✅ Imagem Restaurada")

    gr.Markdown("""
    ### 💡 Dicas:
    - Funciona melhor com fotos de rostos frontais
    - Aceita imagens de baixa qualidade, antigas ou borradas
    - O processamento pode levar alguns segundos
    """)

    # Conectar eventos
    process_btn.click(
        fn=enhance_face,
        inputs=[input_img, version_select, upscale_select],
        outputs=output_img
    )

if __name__ == "__main__":
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )
