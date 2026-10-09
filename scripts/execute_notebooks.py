"""Execute publication notebooks with fresh kernels of this Python environment."""
from pathlib import Path
import argparse,json,sys,tempfile
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='artifacts/notebooks');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='alpha-kernel-') as temporary:
        k=Path(temporary)/'kernels/alpha-release';k.mkdir(parents=True)
        (k/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Alpha release',language='python')))
        manager=KernelSpecManager(kernel_dirs=[str(k.parent)])
        for path in sorted((root/'notebooks').glob('*.ipynb')):
            nb=nbformat.read(path,as_version=4)
            client=NotebookClient(nb,timeout=300,kernel_name='alpha-release',resources={'metadata':{'path':str(out)}})
            client.km=__import__('jupyter_client').KernelManager(kernel_name='alpha-release',kernel_spec_manager=manager)
            client.execute()
            assert not any(o.get('output_type')=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
            nbformat.write(nb,out/path.name);print('PASS:',path.name)
if __name__=='__main__':main()
