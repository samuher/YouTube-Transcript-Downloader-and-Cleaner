"""Launch the local web application with python -m transcript_studio."""
import argparse
import threading
import webbrowser


def main():
    parser=argparse.ArgumentParser(description='Abre Transcript Studio en tu navegador')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--data-dir',help='Carpeta privada para SQLite y preferencias')
    args=parser.parse_args()
    if not 1024<=args.port<=65535:
        parser.error('El puerto debe estar entre 1024 y 65535')
    import uvicorn
    from .app import create_app
    url=f'http://127.0.0.1:{args.port}'
    if not args.no_browser:
        threading.Timer(1.5,lambda:webbrowser.open(url)).start()
    print(f'Transcript Studio: {url} (Ctrl+C para salir)')
    uvicorn.run(create_app(data_dir=args.data_dir),host='127.0.0.1',port=args.port,
                proxy_headers=False,access_log=False)

if __name__=='__main__':
    main()
