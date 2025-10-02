
import gradio as gr
import os
import subprocess
import uuid

def enhance_face(input_image):
    unique_id = str(uuid.uuid4())
    input_path = f"input_{unique_id}.png"
    output_dir = f"output_{unique_id}"
    output_path = os.path.join(output_dir, "restored_imgs", f"input_{unique_id}.png")
    input_image.save(input_path)
    os.makedirs(output_dir, exist_ok=True)
    command = [
        "python", "inference_gfpgan.py",
        "-i", input_path,
        "-o", output_dir,
        "-v", "1.3",
        "-s", "2"
    ]
    try:
        print(f"[GFPGAN] Rodando comando: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        print(f"[GFPGAN] STDOUT:\n{result.stdout}")
        print(f"[GFPGAN] STDERR:\n{result.stderr}")
        if result.returncode != 0:
            print(f"[GFPGAN] Processo retornou código {result.returncode}")
            return gr.update(value=None, visible=False, label=f"Erro ao rodar GFPGAN: {result.stderr}")
        print(f"[GFPGAN] Esperando arquivo de saída: {output_path}")
        if os.path.exists(output_path):
            # Verifica se é uma imagem válida
            try:
                from PIL import Image
                img = Image.open(output_path)
                img.verify()
                print(f"[GFPGAN] Imagem restaurada gerada com sucesso: {output_path}")
                return output_path
            except Exception as img_err:
                print(f"[GFPGAN] Arquivo de saída não é uma imagem válida: {img_err}")
                return gr.update(value=None, visible=False, label="Erro: Arquivo de saída inválido.")
        else:
            print(f"[GFPGAN] Arquivo de saída não encontrado: {output_path}")
            return gr.update(value=None, visible=False, label="Erro: Não foi possível restaurar a imagem.")
    except Exception as e:
        print(f"[GFPGAN] Erro ao rodar GFPGAN: {e}")
    return gr.update(value=None, visible=False, label=f"Erro ao processar: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


demo = gr.Interface(
    fn=enhance_face,
    inputs=gr.Image(type="pil", label="Imagem de entrada"),
    outputs=gr.Image(type="filepath", label="Imagem restaurada"),
    title="GFPGAN - Restauração Facial",
    description="Faça upload de uma foto de rosto para restaurar com GFPGAN.",
    allow_flagging="never"
)

if __name__ == "__main__":
    demo.launch()