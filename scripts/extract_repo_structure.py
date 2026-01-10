#!/usr/bin/env python3
"""
GitHub Repository Structure Extractor
Extrae la estructura interna y componentes de repositorios de GitHub
"""

import requests
import json
import os
import sys
import base64
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import argparse


class GitHubRepoStructureExtractor:
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el extractor con un token de GitHub

        Args:
            token: Personal Access Token de GitHub
        """
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

    def get_repository_info(self, owner: str, repo: str) -> Dict:
        """
        Obtiene información básica del repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio

        Returns:
            Dict con información del repositorio
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener información del repositorio {owner}/{repo}: {e}")
            return {}

    def get_repository_languages(self, owner: str, repo: str) -> Dict:
        """
        Obtiene los lenguajes de programación usados en el repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio

        Returns:
            Dict con lenguajes y sus bytes de código
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/languages"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener lenguajes: {e}")
            return {}

    def get_repository_topics(self, owner: str, repo: str) -> List[str]:
        """
        Obtiene los topics/tags del repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio

        Returns:
            Lista de topics
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/topics"
        headers = self.headers.copy()
        headers['Accept'] = 'application/vnd.github.mercy-preview+json'

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('names', [])
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener topics: {e}")
            return []

    def get_file_tree(self, owner: str, repo: str, branch: str = None, max_depth: int = 5) -> Dict:
        """
        Obtiene el árbol de archivos y directorios del repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            branch: Rama a analizar (default: rama por defecto del repo)
            max_depth: Profundidad máxima del árbol

        Returns:
            Dict con el árbol de archivos
        """
        # Primero obtener el SHA del último commit de la rama
        if not branch:
            repo_info = self.get_repository_info(owner, repo)
            branch = repo_info.get('default_branch', 'main')

        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}"
        params = {'recursive': '1'}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            tree_data = response.json()

            # Organizar en estructura jerárquica
            tree_structure = self._organize_tree_structure(tree_data.get('tree', []), max_depth)

            return {
                'sha': tree_data.get('sha'),
                'url': tree_data.get('url'),
                'tree': tree_structure,
                'truncated': tree_data.get('truncated', False)
            }
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener árbol de archivos: {e}")
            return {}

    def _organize_tree_structure(self, tree_items: List[Dict], max_depth: int) -> Dict:
        """
        Organiza los items del árbol en una estructura jerárquica

        Args:
            tree_items: Lista de items del árbol
            max_depth: Profundidad máxima

        Returns:
            Estructura organizada del árbol
        """
        structure = {
            'files': [],
            'directories': [],
            'total_files': 0,
            'total_dirs': 0,
            'file_extensions': defaultdict(int),
            'file_by_type': defaultdict(list)
        }

        for item in tree_items:
            path = item.get('path', '')
            depth = path.count('/')

            if depth > max_depth:
                continue

            item_info = {
                'path': path,
                'type': item.get('type'),
                'sha': item.get('sha'),
                'size': item.get('size'),
                'url': item.get('url')
            }

            if item.get('type') == 'blob':  # archivo
                structure['files'].append(item_info)
                structure['total_files'] += 1

                # Contar extensiones
                if '.' in path:
                    ext = path.split('.')[-1].lower()
                    structure['file_extensions'][ext] += 1
                    structure['file_by_type'][ext].append(path)

            elif item.get('type') == 'tree':  # directorio
                structure['directories'].append(item_info)
                structure['total_dirs'] += 1

        # Convertir defaultdict a dict normal para JSON
        structure['file_extensions'] = dict(structure['file_extensions'])
        structure['file_by_type'] = dict(structure['file_by_type'])

        return structure

    def get_file_content(self, owner: str, repo: str, file_path: str, branch: str = None) -> Optional[str]:
        """
        Obtiene el contenido de un archivo específico

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            file_path: Ruta del archivo
            branch: Rama (opcional)

        Returns:
            Contenido del archivo como string
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        params = {}
        if branch:
            params['ref'] = branch

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            content_data = response.json()

            if content_data.get('encoding') == 'base64':
                content = base64.b64decode(content_data['content']).decode('utf-8', errors='ignore')
                return content

            return content_data.get('content', '')
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener contenido de {file_path}: {e}")
            return None

    def get_package_dependencies(self, owner: str, repo: str, branch: str = None) -> Dict:
        """
        Extrae dependencias de archivos de configuración comunes

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            branch: Rama (opcional)

        Returns:
            Dict con las dependencias encontradas
        """
        dependencies = {
            'package_managers': [],
            'dependencies_files': {}
        }

        # Archivos de dependencias comunes
        dependency_files = {
            'package.json': 'npm/node',
            'requirements.txt': 'pip/python',
            'Pipfile': 'pipenv/python',
            'setup.py': 'setuptools/python',
            'pom.xml': 'maven/java',
            'build.gradle': 'gradle/java',
            'build.gradle.kts': 'gradle/kotlin',
            'Gemfile': 'bundler/ruby',
            'composer.json': 'composer/php',
            'go.mod': 'go modules',
            'Cargo.toml': 'cargo/rust',
            'mix.exs': 'mix/elixir',
            'Package.swift': 'swift package manager'
        }

        for file_name, package_manager in dependency_files.items():
            content = self.get_file_content(owner, repo, file_name, branch)
            if content:
                dependencies['package_managers'].append(package_manager)
                dependencies['dependencies_files'][file_name] = {
                    'package_manager': package_manager,
                    'content': content[:5000],  # Limitar tamaño
                    'content_truncated': len(content) > 5000
                }

        return dependencies

    def get_config_files(self, owner: str, repo: str, branch: str = None) -> Dict:
        """
        Extrae archivos de configuración importantes

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            branch: Rama (opcional)

        Returns:
            Dict con archivos de configuración
        """
        config_files = {}

        # Archivos de configuración comunes
        config_file_names = [
            '.gitignore',
            '.dockerignore',
            'Dockerfile',
            'docker-compose.yml',
            '.travis.yml',
            '.gitlab-ci.yml',
            'Makefile',
            'CMakeLists.txt',
            '.editorconfig',
            'tsconfig.json',
            'jest.config.js',
            'webpack.config.js',
            'babel.config.js',
            '.eslintrc.json',
            '.prettierrc',
            'pytest.ini',
            'tox.ini',
            'setup.cfg'
        ]

        for file_name in config_file_names:
            content = self.get_file_content(owner, repo, file_name, branch)
            if content:
                config_files[file_name] = {
                    'content': content[:3000],  # Limitar tamaño
                    'content_truncated': len(content) > 3000,
                    'size': len(content)
                }

        return config_files

    def get_readme(self, owner: str, repo: str) -> Dict:
        """
        Obtiene el README del repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio

        Returns:
            Dict con información del README
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            readme_data = response.json()

            content = ""
            if readme_data.get('encoding') == 'base64':
                content = base64.b64decode(readme_data['content']).decode('utf-8', errors='ignore')

            return {
                'name': readme_data.get('name'),
                'path': readme_data.get('path'),
                'size': readme_data.get('size'),
                'content': content[:10000],  # Limitar a 10KB
                'content_truncated': len(content) > 10000,
                'html_url': readme_data.get('html_url')
            }
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener README: {e}")
            return {}

    def get_contributors(self, owner: str, repo: str, max_contributors: int = 20) -> List[Dict]:
        """
        Obtiene los principales contribuidores del repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            max_contributors: Número máximo de contribuidores

        Returns:
            Lista de contribuidores
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
        params = {'per_page': max_contributors}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            contributors = response.json()

            return [{
                'login': c.get('login'),
                'contributions': c.get('contributions'),
                'avatar_url': c.get('avatar_url'),
                'url': c.get('html_url')
            } for c in contributors]
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener contribuidores: {e}")
            return []

    def get_directory_structure_summary(self, tree_structure: Dict) -> Dict:
        """
        Genera un resumen de la estructura de directorios

        Args:
            tree_structure: Estructura del árbol de archivos

        Returns:
            Dict con resumen de la estructura
        """
        # Analizar directorios principales
        root_dirs = set()
        for dir_info in tree_structure.get('directories', []):
            path = dir_info.get('path', '')
            if '/' in path:
                root_dir = path.split('/')[0]
            else:
                root_dir = path
            root_dirs.add(root_dir)

        # Analizar archivos en raíz
        root_files = []
        for file_info in tree_structure.get('files', []):
            path = file_info.get('path', '')
            if '/' not in path:
                root_files.append(path)

        return {
            'root_directories': sorted(list(root_dirs)),
            'root_files': sorted(root_files),
            'total_root_dirs': len(root_dirs),
            'total_root_files': len(root_files)
        }

    def extract_repository_structure(self, owner: str, repo: str,
                                    include_tree: bool = True,
                                    include_dependencies: bool = True,
                                    include_config: bool = True,
                                    include_readme: bool = True,
                                    include_contributors: bool = True,
                                    max_tree_depth: int = 5) -> Dict:
        """
        Extrae toda la estructura del repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            include_tree: Incluir árbol de archivos
            include_dependencies: Incluir archivos de dependencias
            include_config: Incluir archivos de configuración
            include_readme: Incluir README
            include_contributors: Incluir contribuidores
            max_tree_depth: Profundidad máxima del árbol

        Returns:
            Dict completo con toda la estructura
        """
        print(f"\n=== Extrayendo estructura de {owner}/{repo} ===")

        # Información básica del repositorio
        print("  - Obteniendo información básica...")
        repo_info = self.get_repository_info(owner, repo)

        if not repo_info:
            print(f"  ✗ No se pudo obtener información del repositorio")
            return {}

        structure = {
            'repository': {
                'full_name': repo_info.get('full_name'),
                'name': repo_info.get('name'),
                'owner': {
                    'login': repo_info.get('owner', {}).get('login'),
                    'type': repo_info.get('owner', {}).get('type')
                },
                'description': repo_info.get('description'),
                'default_branch': repo_info.get('default_branch'),
                'created_at': repo_info.get('created_at'),
                'updated_at': repo_info.get('updated_at'),
                'pushed_at': repo_info.get('pushed_at'),
                'size': repo_info.get('size'),
                'stargazers_count': repo_info.get('stargazers_count'),
                'watchers_count': repo_info.get('watchers_count'),
                'forks_count': repo_info.get('forks_count'),
                'open_issues_count': repo_info.get('open_issues_count'),
                'is_fork': repo_info.get('fork'),
                'is_archived': repo_info.get('archived'),
                'is_private': repo_info.get('private'),
                'license': repo_info.get('license', {}).get('name') if repo_info.get('license') else None,
                'homepage': repo_info.get('homepage'),
                'html_url': repo_info.get('html_url'),
                'clone_url': repo_info.get('clone_url'),
                'has_wiki': repo_info.get('has_wiki'),
                'has_issues': repo_info.get('has_issues'),
                'has_projects': repo_info.get('has_projects'),
                'has_discussions': repo_info.get('has_discussions')
            },
            'extracted_at': datetime.now().isoformat()
        }

        # Lenguajes
        print("  - Obteniendo lenguajes...")
        languages = self.get_repository_languages(owner, repo)
        if languages:
            total_bytes = sum(languages.values())
            structure['languages'] = {
                'languages': languages,
                'percentages': {lang: round((bytes_count / total_bytes) * 100, 2)
                               for lang, bytes_count in languages.items()},
                'primary_language': max(languages.items(), key=lambda x: x[1])[0] if languages else None
            }

        # Topics
        print("  - Obteniendo topics...")
        topics = self.get_repository_topics(owner, repo)
        if topics:
            structure['topics'] = topics

        # Árbol de archivos
        if include_tree:
            print("  - Obteniendo árbol de archivos...")
            tree_data = self.get_file_tree(owner, repo, max_depth=max_tree_depth)
            if tree_data:
                structure['file_tree'] = tree_data
                structure['directory_summary'] = self.get_directory_structure_summary(
                    tree_data.get('tree', {})
                )

        # README
        if include_readme:
            print("  - Obteniendo README...")
            readme = self.get_readme(owner, repo)
            if readme:
                structure['readme'] = readme

        # Dependencias
        if include_dependencies:
            print("  - Extrayendo dependencias...")
            dependencies = self.get_package_dependencies(
                owner, repo, repo_info.get('default_branch')
            )
            if dependencies.get('package_managers'):
                structure['dependencies'] = dependencies

        # Archivos de configuración
        if include_config:
            print("  - Extrayendo archivos de configuración...")
            config_files = self.get_config_files(
                owner, repo, repo_info.get('default_branch')
            )
            if config_files:
                structure['config_files'] = config_files

        # Contribuidores
        if include_contributors:
            print("  - Obteniendo contribuidores...")
            contributors = self.get_contributors(owner, repo)
            if contributors:
                structure['contributors'] = {
                    'total_shown': len(contributors),
                    'top_contributors': contributors
                }

        print(f"  ✓ Estructura extraída exitosamente")

        return structure

    def extract_multiple_repositories(self, repositories: List[str], **kwargs) -> Dict[str, Dict]:
        """
        Extrae la estructura de múltiples repositorios

        Args:
            repositories: Lista de repositorios en formato "owner/repo"
            **kwargs: Argumentos adicionales para extract_repository_structure

        Returns:
            Dict con estructuras organizadas por repositorio
        """
        all_structures = {}

        for repo_full_name in repositories:
            try:
                owner, repo = repo_full_name.split('/', 1)
            except ValueError:
                print(f"Formato inválido para repositorio: {repo_full_name}. Debe ser 'owner/repo'")
                continue

            structure = self.extract_repository_structure(owner, repo, **kwargs)
            if structure:
                all_structures[repo_full_name] = structure

        return all_structures

    def save_structures_individually(self, structures: Dict[str, Dict],
                                    output_dir: str = "repo_structures"):
        """
        Guarda cada estructura de repositorio en un archivo individual

        Args:
            structures: Dict con estructuras por repositorio
            output_dir: Directorio de salida
        """
        try:
            os.makedirs(output_dir, exist_ok=True)

            for repo_name, structure in structures.items():
                safe_name = repo_name.replace('/', '_').replace('-', '_')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{output_dir}/{safe_name}_structure_{timestamp}.json"

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(structure, f, indent=2, ensure_ascii=False)

                print(f"\n✓ Guardado: {filename}")
                print(f"  Repositorio: {repo_name}")
                if 'file_tree' in structure:
                    tree = structure['file_tree'].get('tree', {})
                    print(f"  Archivos: {tree.get('total_files', 0)}")
                    print(f"  Directorios: {tree.get('total_dirs', 0)}")

        except Exception as e:
            print(f"Error al guardar estructuras: {e}")

    def save_structures_combined(self, structures: Dict[str, Dict],
                                output_file: str = None):
        """
        Guarda todas las estructuras en un archivo único

        Args:
            structures: Dict con estructuras por repositorio
            output_file: Nombre del archivo de salida
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"all_repositories_structure_{timestamp}.json"

        try:
            data = {
                'extracted_at': datetime.now().isoformat(),
                'total_repositories': len(structures),
                'repositories': structures
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Todas las estructuras guardadas en: {output_file}")
            print(f"  Total de repositorios: {len(structures)}")

        except Exception as e:
            print(f"Error al guardar archivo combinado: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Extrae la estructura interna de repositorios de GitHub'
    )
    parser.add_argument('--repos', nargs='+', required=True,
                       help='Lista de repositorios en formato owner/repo')
    parser.add_argument('--token', help='Token de GitHub (recomendado)',
                       default=os.getenv('GITHUB_TOKEN'))
    parser.add_argument('--output-dir', default='repo_structures',
                       help='Directorio de salida para archivos individuales')
    parser.add_argument('--combined', action='store_true',
                       help='Guardar todo en un archivo único')
    parser.add_argument('--output-file',
                       help='Nombre del archivo de salida (para --combined)')
    parser.add_argument('--no-tree', action='store_true',
                       help='No incluir árbol de archivos')
    parser.add_argument('--no-dependencies', action='store_true',
                       help='No incluir archivos de dependencias')
    parser.add_argument('--no-config', action='store_true',
                       help='No incluir archivos de configuración')
    parser.add_argument('--no-readme', action='store_true',
                       help='No incluir README')
    parser.add_argument('--no-contributors', action='store_true',
                       help='No incluir contribuidores')
    parser.add_argument('--max-depth', type=int, default=5,
                       help='Profundidad máxima del árbol de archivos (default: 5)')

    args = parser.parse_args()

    # Validar repositorios
    valid_repos = []
    for repo in args.repos:
        if '/' not in repo:
            print(f"Formato inválido: {repo}. Debe ser 'owner/repo'")
            continue
        valid_repos.append(repo)

    if not valid_repos:
        print("No se proporcionaron repositorios válidos")
        return

    print(f"Procesando {len(valid_repos)} repositorio(s):")
    for repo in valid_repos:
        print(f"  - {repo}")

    # Crear extractor
    extractor = GitHubRepoStructureExtractor(token=args.token)

    # Extraer estructuras
    structures = extractor.extract_multiple_repositories(
        repositories=valid_repos,
        include_tree=not args.no_tree,
        include_dependencies=not args.no_dependencies,
        include_config=not args.no_config,
        include_readme=not args.no_readme,
        include_contributors=not args.no_contributors,
        max_tree_depth=args.max_depth
    )

    if not structures:
        print("\nNo se pudo extraer ninguna estructura")
        return

    # Guardar resultados
    if args.combined:
        extractor.save_structures_combined(structures, args.output_file)
    else:
        extractor.save_structures_individually(structures, args.output_dir)

    print(f"\n=== EXTRACCIÓN COMPLETADA ===")
    print(f"Repositorios procesados: {len(structures)}")


if __name__ == "__main__":
    main()
