import os
import sys
import psutil
import asyncio
import requests
from xml.etree import ElementTree
from urllib.parse import urlparse
import re

__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")
__docs__ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

# Adiciona o diretório pai ao caminho do sistema
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

def save_to_markdown(url: str, content: str):
    """
    Salva o conteúdo markdown em um arquivo baseado na URL.
    """
    # Cria a pasta docs se não existir
    os.makedirs(__docs__, exist_ok=True)
    
    # Gera um nome de arquivo seguro baseado na URL
    parsed_url = urlparse(url)
    file_name = parsed_url.path.strip('/')
    if not file_name:
        file_name = 'index'
    else:
        # Remove caracteres inválidos e substitui / por _
        file_name = re.sub(r'[^\w\-_]', '_', file_name.replace('/', '_'))
    
    file_path = os.path.join(__docs__, f"{file_name}.md")
    
    # Salva o conteúdo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"<!-- URL: {url} -->\n\n")
        f.write(content)
    
    print(f"Salvo: {file_path}")

def create_readme(urls_processadas: List[tuple[str, bool]]):
    """
    Cria um README.md na pasta docs listando todas as páginas processadas.
    """
    readme_path = os.path.join(__docs__, "README.md")
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("# Documentação\n\n")
        f.write("Lista de todas as páginas documentadas:\n\n")
        
        # Agrupa por status
        sucesso = []
        falhas = []
        for url, status in urls_processadas:
            parsed_url = urlparse(url)
            file_name = parsed_url.path.strip('/')
            if not file_name:
                file_name = 'index'
            else:
                file_name = re.sub(r'[^\w\-_]', '_', file_name.replace('/', '_'))
            
            if status:
                sucesso.append((url, file_name))
            else:
                falhas.append(url)
        
        # Lista páginas com sucesso
        f.write("## Páginas Processadas\n\n")
        for url, file_name in sorted(sucesso):
            f.write(f"- [{url}](./{file_name}.md)\n")
        
        # Lista falhas se houver
        if falhas:
            f.write("\n## Falhas no Processamento\n\n")
            for url in sorted(falhas):
                f.write(f"- {url}\n")
    
    print(f"\nREADME.md criado em: {readme_path}")

async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    print("\n=== Rastreamento Paralelo com Reuso de Navegador + Verificação de Memória ===")

    # Vamos manter o controle do pico de uso de memória em todas as tarefas
    pico_memoria = 0
    processo = psutil.Process(os.getpid())
    urls_processadas: List[tuple[str, bool]] = []

    def registrar_memoria(prefixo: str = ""):
        nonlocal pico_memoria
        memoria_atual = processo.memory_info().rss  # em bytes
        if memoria_atual > pico_memoria:
            pico_memoria = memoria_atual
        print(f"{prefixo} Memória Atual: {memoria_atual // (1024 * 1024)} MB, Pico: {pico_memoria // (1024 * 1024)} MB")

    # Configuração mínima do navegador
    config_navegador = BrowserConfig(
        headless=True,
        verbose=False,   # corrigido de 'verbos=False'
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    config_rastreamento = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Cria a instância do rastreador
    rastreador = AsyncWebCrawler(config=config_navegador)
    await rastreador.start()

    try:
        # Vamos dividir as URLs em lotes de 'max_concurrent'
        contador_sucesso = 0
        contador_falha = 0
        for i in range(0, len(urls), max_concurrent):
            lote = urls[i : i + max_concurrent]
            tarefas = []

            for j, url in enumerate(lote):
                # ID de sessão único por subtarefa concorrente
                id_sessao = f"sessao_paralela_{i + j}"
                tarefa = rastreador.arun(url=url, config=config_rastreamento, session_id=id_sessao)
                tarefas.append(tarefa)

            # Verifica o uso de memória antes de iniciar as tarefas
            registrar_memoria(prefixo=f"Antes do lote {i//max_concurrent + 1}: ")

            # Coleta resultados
            resultados = await asyncio.gather(*tarefas, return_exceptions=True)

            # Verifica o uso de memória após completar as tarefas
            registrar_memoria(prefixo=f"Depois do lote {i//max_concurrent + 1}: ")

            # Avalia resultados
            for url, resultado in zip(lote, resultados):
                if isinstance(resultado, Exception):
                    print(f"Erro ao rastrear {url}: {resultado}")
                    contador_falha += 1
                    urls_processadas.append((url, False))
                elif resultado.success:
                    save_to_markdown(url, resultado.markdown)
                    contador_sucesso += 1
                    urls_processadas.append((url, True))
                else:
                    contador_falha += 1
                    urls_processadas.append((url, False))

        print(f"\nResumo:")
        print(f"  - Rastreados com sucesso: {contador_sucesso}")
        print(f"  - Falhas: {contador_falha}")
        
        # Cria o README.md com a lista de todas as páginas
        create_readme(urls_processadas)

    finally:
        print("\nFechando rastreador...")
        await rastreador.close()
        # Registro final de memória
        registrar_memoria(prefixo="Final: ")
        print(f"\nPico de uso de memória (MB): {pico_memoria // (1024 * 1024)}")

def get_sitemap_urls(sitemap_url: str) -> List[str]:
    """
    Busca todas as URLs de um sitemap XML.
    
    Args:
        sitemap_url: URL do sitemap (ex: https://site.com/sitemap.xml)
    
    Returns:
        List[str]: Lista de URLs encontradas
    """            
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Analisa o XML
        root = ElementTree.fromstring(response.content)
        
        # Extrai todas as URLs do sitemap
        # O namespace geralmente é definido no elemento raiz
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        return urls
    except Exception as e:
        print(f"Erro ao buscar sitemap: {e}")
        return []        

async def main():
    # Solicita a URL do sitemap ao usuário
    sitemap_url = input("Digite a URL do sitemap (ex: https://site.com/sitemap.xml): ")
    
    urls = get_sitemap_urls(sitemap_url)
    if urls:
        print(f"Encontradas {len(urls)} URLs para rastrear")
        await crawl_parallel(urls, max_concurrent=10)
    else:
        print("Nenhuma URL encontrada para rastrear")    

if __name__ == "__main__":
    asyncio.run(main())
