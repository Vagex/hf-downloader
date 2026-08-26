import os
import json

workflow_path = r'C:\Users\Administrator\Documents\antigravity\wonderful-salk\minimax_h3_r2v_latent_upscaler_workflow.json'
with open(workflow_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes_in_wf = set(n.get('type') for n in wf.get('nodes', []))

custom_nodes_dirs = [
    r'C:\Users\Administrator\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\custom_nodes',
    r'F:\ComfyUI-aki-v3\ComfyUI\custom_nodes'
]

core_nodes = {
    'BasicGuider', 'BasicScheduler', 'CFGGuider', 'CLIPLoader', 'ConditioningZeroOut', 
    'CreateVideo', 'KSamplerSelect', 'LTXVConcatAVLatent', 'LTXVSeparateAVLatent', 
    'LoadImage', 'LoraLoaderModelOnly', 'ManualSigmas', 'RandomNoise', 
    'SamplerCustomAdvanced', 'SaveVideo', 'SplitSigmas', 'UNETLoader', 'VAEDecode', 
    'VAEDecodeAudio', 'VAELoader', 'PrimitiveFloat', 'PrimitiveStringMultiline', 'MarkdownNote'
}

found_nodes = set(core_nodes)

for c_dir in custom_nodes_dirs:
    for root, dirs, files in os.walk(c_dir):
        for file in files:
            if file.endswith('.py'):
                p = os.path.join(root, file)
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for node in nodes_in_wf:
                            if f'"{node}"' in content or f"'{node}'" in content:
                                found_nodes.add(node)
                except:
                    pass

missing = nodes_in_wf - found_nodes
print("Total unique nodes in workflow:", len(nodes_in_wf))
print("Found nodes:", len(found_nodes.intersection(nodes_in_wf)))
print("Missing nodes list:", sorted(list(missing)))
