import gradio as gr
import os
from inference_gfpgan import main as gfpgan_infer

def enhance_face(input_image):
    input_path = "input_temp.png"
    output_path = "output_temp.png"
    input_image.save(input_path)
    # Chama o script de inferência do GFPGAN
    # Ajuste os argumentos conforme necessário para o seu setup
    args = [
        "--input", input_path,
        "--output", output_path,
        "--model_path", "experiments/pretrained_models/GFPGANv1.3.pth"
    ]
    gfpgan_infer(args)
    if os.path.exists(output_path):
        return output_path
    else:
        return None

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