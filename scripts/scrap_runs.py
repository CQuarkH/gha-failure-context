#!/usr/bin/env python3
"""
GitHub Workflow Runs Extractor - Versión 3 (Job-Level Logs)
Extrae información de workflow runs de múltiples repositorios de GitHub
con logs a nivel de job individual

Uso (ejemplo):

python scrap_formated_runsv3.py --repos django/django facebook/react spring-projects/spring-framework pallets/flask expressjs/express --max-runs-per-workflow 1 --token TOKEN

"""

from collections import defaultdict
import requests
import json
import os
import sys
import re
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

class GitHubRunsExtractor:
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el extractor con un token de GitHub (opcional pero recomendado)

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

    def get_all_workflows(self, owner: str, repo: str) -> List[Dict]:
        """
        Obtiene todos los workflows de un repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio

        Returns:
            Lista de workflows disponibles
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            workflows_data = response.json()
            return workflows_data.get('workflows', [])
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener workflows de {owner}/{repo}: {e}")
            return []

    def get_workflow_runs(self, owner: str, repo: str, per_page: int = 100, page: int = 1) -> Dict:
        """
        Obtiene los workflow runs de un repositorio

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            per_page: Número de resultados por página (máximo 100)
            page: Número de página

        Returns:
            Dict con la respuesta de la API
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        params = {
            'per_page': per_page,
            'page': page
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener runs: {e}")
            return {}

    def get_workflow_runs_by_workflow_id(self, owner: str, repo: str, workflow_id: int, per_page: int = 100, page: int = 1) -> Dict:
        """
        Obtiene los workflow runs de un workflow específico

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            workflow_id: ID del workflow
            per_page: Número de resultados por página (máximo 100)
            page: Número de página

        Returns:
            Dict con la respuesta de la API
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        params = {
            'per_page': per_page,
            'page': page
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener runs del workflow {workflow_id}: {e}")
            return {}

    def get_workflow_details(self, owner: str, repo: str, workflow_id: int) -> Dict:
        """
        Obtiene detalles de un workflow específico

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            workflow_id: ID del workflow

        Returns:
            Dict con información del workflow
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener workflow {workflow_id}: {e}")
            return {}

    def get_workflow_content(self, owner: str, repo: str, workflow_path: str, ref: str = "main") -> str:
        """
        Obtiene el contenido del archivo de workflow YAML

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            workflow_path: Ruta del archivo de workflow
            ref: Rama o commit (por defecto main)

        Returns:
            Contenido del archivo YAML como string
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{workflow_path}"
        params = {'ref': ref}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            content_data = response.json()

            if content_data.get('encoding') == 'base64':
                import base64
                content = base64.b64decode(content_data['content']).decode('utf-8')
                return content

            return content_data.get('content', '')
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener contenido del workflow {workflow_path}: {e}")
            return ""

    def parse_workflow_yaml(self, yaml_content: str) -> Dict:
        """
        Parsea el contenido YAML del workflow

        Args:
            yaml_content: Contenido del archivo YAML

        Returns:
            Diccionario con la estructura del workflow parseada
        """
        try:
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"Error al parsear YAML: {e}")
            return {}

    def get_job_dependencies(self, workflow_yaml: Dict, job_name: str) -> List[str]:
        """
        Extrae las dependencias (needs) de un job específico desde el YAML del workflow

        Args:
            workflow_yaml: Contenido parseado del workflow YAML
            job_name: Nombre del job del cual extraer dependencias

        Returns:
            Lista de nombres de jobs de los cuales depende este job
        """
        jobs = workflow_yaml.get('jobs', {})
        dependencies = []

        # 1) Buscar por clave exacta del job
        if job_name in jobs:
            job_data = jobs[job_name]
            needs = job_data.get('needs', [])

            # 'needs' puede ser un string (un solo job) o una lista
            if isinstance(needs, str):
                dependencies = [needs]
            elif isinstance(needs, list):
                dependencies = needs

            return dependencies

        # 2) Buscar por el campo 'name' del job
        for job_id, job_data in jobs.items():
            if job_data.get('name') == job_name:
                needs = job_data.get('needs', [])

                if isinstance(needs, str):
                    dependencies = [needs]
                elif isinstance(needs, list):
                    dependencies = needs

                return dependencies

        # 3) Fallback a matching parcial por nombre
        for job_id, job_data in jobs.items():
            job_display_name = job_data.get('name', '')
            if job_name.lower() in str(job_display_name).lower():
                needs = job_data.get('needs', [])

                if isinstance(needs, str):
                    dependencies = [needs]
                elif isinstance(needs, list):
                    dependencies = needs

                return dependencies

        return dependencies

    def get_run_jobs(self, owner: str, repo: str, run_id: int, attempt_number: int = 1) -> List[Dict]:
        """
        Obtiene los jobs de un run específico para un attempt dado

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            run_id: ID del run
            attempt_number: Número del attempt (por defecto 1)

        Returns:
            Lista de jobs
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/jobs"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('jobs', [])
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener jobs del run {run_id} attempt {attempt_number}: {e}")
            return []

    def check_logs_available(self, owner: str, repo: str, job_id: int) -> bool:
        """
        Verifica si los logs están disponibles para un job específico

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            job_id: ID del job

        Returns:
            True si los logs están disponibles, False en caso contrario
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"

        try:
            response = requests.head(url, headers=self.headers, allow_redirects=True)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_job_logs(self, owner: str, repo: str, job_id: int, job_name: str, run_id: int) -> Optional[str]:
        """
        Obtiene los logs de un job específico y los guarda en el sistema de archivos

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            job_id: ID del job
            job_name: Nombre del job (para crear el directorio)
            run_id: ID del run (para organizar la estructura de carpetas)

        Returns:
            Ruta al archivo de log guardado, o None si hay error
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"

        # Crear estructura de directorios: logs/owner_repo/run_12345678/job_name/
        repo_identifier = f"{owner}_{repo}".replace('-', '_')
        run_logs_base = os.path.join('logs', repo_identifier, f"run_{run_id}")

        # Sanitizar el nombre del job para usarlo como nombre de directorio
        safe_job_name = re.sub(r'[^\w\-_\. ]', '_', job_name)
        job_dir = os.path.join(run_logs_base, safe_job_name)
        os.makedirs(job_dir, exist_ok=True)

        log_file_path = os.path.join(job_dir, f"job_{job_id}_full_log.txt")

        try:
            response = requests.get(url, headers=self.headers, allow_redirects=True)
            response.raise_for_status()

            # Guardar el contenido de texto plano directamente
            log_content = response.text

            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)

            print(f"      ✓ Log guardado: {log_file_path}")
            return log_file_path

        except requests.exceptions.RequestException as e:
            print(f"      ✗ Error al descargar logs del job {job_id}: {e}")
            return None
        except Exception as e:
            print(f"      ✗ Error al guardar logs del job {job_id}: {e}")
            return None

    def get_single_run_attempt(self, owner: str, repo: str, run_id: int, attempt_number: int) -> Dict:
        """
        Obtiene información específica de un attempt individual

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            run_id: ID del run
            attempt_number: Número del attempt

        Returns:
            Información del attempt específico
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener attempt {attempt_number} del run {run_id}: {e}")
            return {}

    def get_run_attempts(self, owner: str, repo: str, run_id: int) -> List[Dict]:
        """
        Obtiene todos los attempts de un run específico

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            run_id: ID del run

        Returns:
            Lista de attempts
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/attempts"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 404:
                # Si no hay endpoint de attempts, crear uno basado en el run original
                return [{'run_attempt': 1}]
            response.raise_for_status()
            return response.json().get('attempts', [])
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener attempts del run {run_id}: {e}")
            # Fallback: asumir que hay al menos 1 attempt
            return [{'run_attempt': 1}]

    def process_run_data(self, run_data: Dict, workflow_data: Dict, attempts_data: List[Dict] = None) -> Dict:
        """
        Procesa y estructura los datos del run según el formato requerido con run_attempts

        Args:
            run_data: Datos del run
            workflow_data: Datos del workflow
            attempts_data: Lista de attempts con sus jobs y logs

        Returns:
            Dict con los datos procesados
        """
        processed_run = {
            'id': run_data.get('id'),
            'name': run_data.get('name'),
            'conclusion': run_data.get('conclusion'),
            'status': run_data.get('status'),
            'created_at': run_data.get('created_at'),
            'updated_at': run_data.get('updated_at'),
            'run_started_at': run_data.get('run_started_at'),
            'display_title': run_data.get('display_title'),
            'node_id': run_data.get('node_id'),
            'run_number': run_data.get('run_number'),
            'event': run_data.get('event'),
            'workflow_id': run_data.get('workflow_id'),
            'check_suite_id': run_data.get('check_suite_id'),
            'url': run_data.get('url'),
            'html_url': run_data.get('html_url'),
            'actor': run_data.get('actor', {}),
            'triggering_actor': run_data.get('triggering_actor', {}),
            'head_commit': run_data.get('head_commit', {}),
            'repository': run_data.get('repository', {}),
            'workflow': workflow_data,
            'run_attempts': attempts_data or []
        }

        return processed_run

    def extract_runs_from_multiple_repos(self, repositories: List[str],
                                       max_runs_per_workflow: int = 500,
                                       include_jobs: bool = True,
                                       include_workflow_details: bool = True,
                                       include_logs: bool = True,
                                       only_failures: bool = True,
                                       verify_logs: bool = True) -> Dict[str, List[Dict]]:
        """
        Extrae runs de múltiples repositorios y todos sus workflows

        Args:
            repositories: Lista de repositorios en formato "owner/repo"
            max_runs_per_workflow: Número máximo de runs a extraer por workflow
            include_jobs: Si incluir información de jobs
            include_workflow_details: Si incluir detalles del workflow
            include_logs: Si incluir logs de los jobs
            only_failures: Si solo procesar runs con conclusion=failure
            verify_logs: Si verificar disponibilidad de logs antes de procesar

        Returns:
            Dict con los runs organizados por repositorio
        """
        all_repos_data = {}

        for repo_full_name in repositories:
            try:
                owner, repo = repo_full_name.split('/', 1)
            except ValueError:
                print(f"Formato inválido para repositorio: {repo_full_name}. Debe ser 'owner/repo'")
                continue

            print(f"\n=== Procesando repositorio: {repo_full_name} ===")

            # Obtener todos los workflows del repositorio
            workflows = self.get_all_workflows(owner, repo)
            if not workflows:
                print(f"No se encontraron workflows en {repo_full_name}")
                continue

            print(f"Encontrados {len(workflows)} workflows:")
            for wf in workflows:
                print(f"  - {wf.get('name')} (ID: {wf.get('id')})")

            repo_runs = []

            # Procesar cada workflow
            for workflow in workflows:
                workflow_id = workflow.get('id')
                workflow_name = workflow.get('name', f"Workflow-{workflow_id}")

                print(f"\n--- Procesando workflow: {workflow_name} (ID: {workflow_id}) ---")

                # Extraer runs del workflow específico
                workflow_runs = self.extract_runs_from_single_workflow(
                    owner=owner,
                    repo=repo,
                    workflow_id=workflow_id,
                    max_runs=max_runs_per_workflow,
                    include_jobs=include_jobs,
                    include_workflow_details=include_workflow_details,
                    include_logs=include_logs,
                    only_failures=only_failures,
                    verify_logs=verify_logs
                )

                repo_runs.extend(workflow_runs)
                print(f"Extraídos {len(workflow_runs)} runs del workflow {workflow_name}")

            all_repos_data[repo_full_name] = repo_runs
            print(f"\nTotal runs extraídos de {repo_full_name}: {len(repo_runs)}")

        return all_repos_data

    def extract_runs_from_single_workflow(self, owner: str, repo: str, workflow_id: int,
                                        max_runs: int = 500, include_jobs: bool = True,
                                        include_workflow_details: bool = True,
                                        include_logs: bool = True,
                                        only_failures: bool = True,
                                        verify_logs: bool = True) -> List[Dict]:
        """
        Extrae runs de un workflow específico

        Args:
            owner: Propietario del repositorio
            repo: Nombre del repositorio
            workflow_id: ID del workflow
            max_runs: Número máximo de runs a extraer
            include_jobs: Si incluir información de jobs
            include_workflow_details: Si incluir detalles del workflow
            include_logs: Si incluir logs de los jobs
            only_failures: Si solo procesar runs con conclusion=failure
            verify_logs: Si verificar disponibilidad de logs antes de procesar

        Returns:
            Lista de runs procesados
        """
        workflow_runs = []
        page = 1
        workflow_cache = {}
        workflow_yaml_cache = {}

        while True:
            runs_response = self.get_workflow_runs_by_workflow_id(owner, repo, workflow_id, per_page=100, page=page)

            if not runs_response or 'workflow_runs' not in runs_response:
                break

            runs = runs_response['workflow_runs']

            if not runs:
                break

            for run in runs:
                if max_runs and len(workflow_runs) >= max_runs:
                    break

                # Filtrar runs en progreso
                if run.get('status') in ['in_progress', 'queued', 'waiting', 'pending', 'requested']:
                    continue

                # Filtrar por failures si la flag está activa
                if only_failures and run.get('conclusion') != 'failure':
                    continue

                print(f"  Procesando run {run['id']} - {run['name']} (conclusion: {run.get('conclusion')}) ({len(workflow_runs) + 1})")

                # Obtener detalles del workflow si se solicita
                workflow_data = {}
                workflow_yaml = {}
                if include_workflow_details:
                    workflow_id_key = run['workflow_id']
                    if workflow_id_key not in workflow_cache:
                        workflow_cache[workflow_id_key] = self.get_workflow_details(owner, repo, workflow_id_key)
                    workflow_data = workflow_cache[workflow_id_key]

                    # Obtener contenido YAML del workflow para extraer dependencias
                    workflow_path = workflow_data.get('path', '')
                    if workflow_path and workflow_path not in workflow_yaml_cache:
                        print(f"    Obteniendo contenido YAML del workflow: {workflow_path}")
                        yaml_content = self.get_workflow_content(owner, repo, workflow_path,
                                                            run.get('head_sha', 'main'))
                        if yaml_content:
                            workflow_yaml_cache[workflow_path] = self.parse_workflow_yaml(yaml_content)
                    workflow_yaml = workflow_yaml_cache.get(workflow_path, {})

                # Obtener todos los attempts del run
                attempts_data = []
                if include_jobs:
                    # Determinar el número de attempts
                    max_attempt = run.get('run_attempt', 1)

                    for attempt_num in range(1, max_attempt + 1):
                        print(f"    Procesando attempt {attempt_num}/{max_attempt}")

                        # Obtener jobs del attempt
                        jobs_data = self.get_run_jobs(owner, repo, run['id'], attempt_num)

                        # Procesar jobs del attempt
                        processed_jobs = []
                        for job in jobs_data:
                            job_id = job.get('id')
                            job_name = job.get('name')

                            processed_job = {
                                'id': job_id,
                                'node_id': job.get('node_id'),
                                'run_attempt': job.get('run_attempt'),
                                'name': job_name,
                                'status': job.get('status'),
                                'conclusion': job.get('conclusion'),
                                'created_at': job.get('created_at'),
                                'started_at': job.get('started_at'),
                                'completed_at': job.get('completed_at'),
                                'url': job.get('url'),
                                'html_url': job.get('html_url'),
                                'runner_name': job.get('runner_name'),
                                'labels': job.get('labels', []),
                                'steps': job.get('steps', []),
                                'dependencies': [],
                                'full_log_path': None
                            }

                            # Extraer dependencias del YAML si está disponible
                            if workflow_yaml and job_name:
                                dependencies = self.get_job_dependencies(workflow_yaml, job_name)
                                processed_job['dependencies'] = dependencies
                                if dependencies:
                                    print(f"      Job '{job_name}' depende de: {dependencies}")

                            # Obtener logs del job si se solicita
                            if include_logs:
                                # Verificar disponibilidad de logs si la flag está activa
                                if verify_logs:
                                    logs_available = self.check_logs_available(owner, repo, job_id)
                                    if not logs_available:
                                        print(f"      ⚠ Logs no disponibles para job {job_id} ({job_name})")
                                        processed_jobs.append(processed_job)
                                        continue

                                print(f"      Descargando logs del job {job_id} ({job_name})...")
                                log_path = self.get_job_logs(owner, repo, job_id, job_name, run['id'])
                                processed_job['full_log_path'] = log_path

                            processed_jobs.append(processed_job)

                        # Obtener información del attempt específico
                        attempt_info = self.get_single_run_attempt(owner, repo, run['id'], attempt_num)

                        # Crear el attempt con información específica
                        attempt_data = {
                            'run_attempt': attempt_num,
                            'status': attempt_info.get('status') if attempt_info else (run.get('status') if attempt_num == max_attempt else 'completed'),
                            'conclusion': attempt_info.get('conclusion') if attempt_info else (run.get('conclusion') if attempt_num == max_attempt else 'failure'),
                            'updated_at': attempt_info.get('updated_at') if attempt_info else run.get('updated_at'),
                            'run_started_at': attempt_info.get('run_started_at') if attempt_info else run.get('run_started_at'),
                            'created_at': attempt_info.get('created_at') if attempt_info else run.get('created_at'),
                            'jobs': processed_jobs
                        }

                        attempts_data.append(attempt_data)

                # Procesar y agregar el run
                processed_run = self.process_run_data(run, workflow_data, attempts_data)
                workflow_runs.append(processed_run)

            if max_runs and len(workflow_runs) >= max_runs:
                break

            page += 1

        return workflow_runs

    def save_runs_to_file(self, runs_data: Dict[str, List[Dict]], filename: str = None):
        """
        Guarda los runs de múltiples repositorios en un archivo JSON

        Args:
            runs_data: Dict con runs organizados por repositorio
            filename: Nombre del archivo (opcional)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_multi_repo_runs_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(runs_data, f, indent=2, ensure_ascii=False)

            total_runs = sum(len(runs) for runs in runs_data.values())
            print(f"\nRuns guardados en: {filename}")
            print(f"Total de repositorios: {len(runs_data)}")
            print(f"Total de runs: {total_runs}")

            # Mostrar resumen por repositorio
            for repo, runs in runs_data.items():
                print(f"  {repo}: {len(runs)} runs")

        except Exception as e:
            print(f"Error al guardar archivo: {e}")

    def save_runs_individually_by_repository(self, runs_data: Dict[str, List[Dict]], base_output_dir: str = "multi_repo_output"):
        """
        Guarda cada run en un archivo individual, organizados por repositorio en directorios separados

        Args:
            runs_data: Dict con runs organizados por repositorio
            base_output_dir: Directorio base para la salida
        """
        try:
            os.makedirs(base_output_dir, exist_ok=True)
            total_files_created = 0

            for repo_full_name, runs in runs_data.items():
                # Crear nombre de directorio seguro para el repositorio
                safe_repo_name = repo_full_name.replace('/', '_').replace('-', '_')
                repo_dir = os.path.join(base_output_dir, safe_repo_name)
                os.makedirs(repo_dir, exist_ok=True)

                print(f"\nGuardando runs de {repo_full_name} en {repo_dir}/")

                # Crear archivo de resumen del repositorio
                summary_data = {
                    'repository': repo_full_name,
                    'total_runs': len(runs),
                    'extracted_at': datetime.now().isoformat(),
                    'workflows': {}
                }

                # Agrupar runs por workflow para el resumen
                workflows_summary = defaultdict(list)
                for run in runs:
                    workflow_name = run.get('workflow', {}).get('name', 'Unknown Workflow')
                    workflows_summary[workflow_name].append({
                        'run_id': run.get('id'),
                        'run_number': run.get('run_number'),
                        'status': run.get('status'),
                        'conclusion': run.get('conclusion'),
                        'created_at': run.get('created_at')
                    })

                # Completar resumen de workflows
                for workflow_name, workflow_runs in workflows_summary.items():
                    summary_data['workflows'][workflow_name] = {
                        'total_runs': len(workflow_runs),
                        'runs_summary': workflow_runs
                    }

                # Guardar archivo de resumen
                summary_file = os.path.join(repo_dir, f"{safe_repo_name}_summary.json")
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2, ensure_ascii=False)

                # Guardar cada run individualmente
                for run in runs:
                    run_id = run.get('id')
                    run_number = run.get('run_number', 'unknown')
                    workflow_name = run.get('workflow', {}).get('name', 'unknown_workflow')

                    # Crear nombre de archivo seguro
                    safe_workflow_name = re.sub(r'[^\w\-_]', '_', workflow_name)
                    filename = f"run_{run_id}_number_{run_number}_{safe_workflow_name}.json"
                    file_path = os.path.join(repo_dir, filename)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(run, f, indent=2, ensure_ascii=False)

                    total_files_created += 1

                print(f"  - Creado resumen: {summary_file}")
                print(f"  - Guardados {len(runs)} runs individuales")

            print(f"\n=== RESUMEN FINAL ===")
            print(f"Total de repositorios procesados: {len(runs_data)}")
            print(f"Total de archivos creados: {total_files_created + len(runs_data)} (incluye {len(runs_data)} resúmenes)")
            print(f"Directorio base: {base_output_dir}")

            # Mostrar estructura de directorios creada
            print(f"\nEstructura creada:")
            for repo_full_name, runs in runs_data.items():
                safe_repo_name = repo_full_name.replace('/', '_').replace('-', '_')
                print(f"  {base_output_dir}/{safe_repo_name}/")
                print(f"    ├── {safe_repo_name}_summary.json")
                print(f"    └── {len(runs)} archivos run_*.json")

        except Exception as e:
            print(f"Error al guardar archivos individuales por repositorio: {e}")

    def save_runs_by_repository(self, runs_data: Dict[str, List[Dict]], base_output_dir: str = "multi_repo_output"):
        """
        Guarda todos los runs de cada repositorio en un archivo único por repositorio

        Args:
            runs_data: Dict con runs organizados por repositorio
            base_output_dir: Directorio base para la salida
        """
        try:
            os.makedirs(base_output_dir, exist_ok=True)

            for repo_full_name, runs in runs_data.items():
                # Crear nombre de archivo seguro
                safe_repo_name = repo_full_name.replace('/', '_').replace('-', '_')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{base_output_dir}/{safe_repo_name}_all_runs_{timestamp}.json"

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'repository': repo_full_name,
                        'total_runs': len(runs),
                        'extracted_at': datetime.now().isoformat(),
                        'runs': runs
                    }, f, indent=2, ensure_ascii=False)

                print(f"Guardado {repo_full_name}: {len(runs)} runs en {filename}")

        except Exception as e:
            print(f"Error al guardar archivos por repositorio: {e}")

def main():
    parser = argparse.ArgumentParser(description='Extrae workflow runs de múltiples repositorios de GitHub')
    parser.add_argument('--repos', nargs='+', required=True,
                       help='Lista de repositorios en formato owner/repo')
    parser.add_argument('--token', help='Token de GitHub (recomendado)',
                       default=os.getenv('GITHUB_TOKEN'))
    parser.add_argument('--max-runs-per-workflow', type=int, default=500,
                       help='Número máximo de runs a extraer por workflow (default: 500)')
    parser.add_argument('--output', help='Archivo de salida JSON único para todos los repos')
    parser.add_argument('--individual-files', action='store_true', default=True,
                       help='Guardar cada run en un archivo individual por repositorio (default)')
    parser.add_argument('--combined-files', action='store_true',
                       help='Guardar todos los runs de cada repositorio en un archivo único')
    parser.add_argument('--output-dir', default='multi_repo_output',
                       help='Directorio base para los archivos de salida')
    parser.add_argument('--no-logs', action='store_true',
                       help='No incluir logs de los jobs')
    parser.add_argument('--no-jobs', action='store_true',
                       help='No incluir información de jobs')
    parser.add_argument('--no-workflow', action='store_true',
                       help='No incluir detalles del workflow')
    parser.add_argument('--all-conclusions', action='store_true',
                       help='Procesar runs con cualquier conclusion (por defecto solo failures)')
    parser.add_argument('--no-verify-logs', action='store_true',
                       help='No verificar disponibilidad de logs antes de procesar')

    args = parser.parse_args()

    # Validar formato de repositorios
    valid_repos = []
    for repo in args.repos:
        if '/' not in repo:
            print(f"Formato inválido para repositorio: {repo}. Debe ser 'owner/repo'")
            continue
        valid_repos.append(repo)

    if not valid_repos:
        print("No se proporcionaron repositorios válidos")
        return

    print(f"Procesando {len(valid_repos)} repositorio(s):")
    for repo in valid_repos:
        print(f"  - {repo}")
    print(f"Máximo runs por workflow: {args.max_runs_per_workflow}")
    print(f"Solo failures: {not args.all_conclusions}")
    print(f"Verificar logs: {not args.no_verify_logs}")

    # Crear extractor
    extractor = GitHubRunsExtractor(token=args.token)

    # Extraer runs de múltiples repositorios
    all_runs_data = extractor.extract_runs_from_multiple_repos(
        repositories=valid_repos,
        max_runs_per_workflow=args.max_runs_per_workflow,
        include_jobs=not args.no_jobs,
        include_workflow_details=not args.no_workflow,
        include_logs=not args.no_logs and not args.no_jobs,
        only_failures=not args.all_conclusions,
        verify_logs=not args.no_verify_logs
    )

    if not all_runs_data:
        print("No se encontraron runs en ningún repositorio")
        return

    # Guardar resultados según las opciones elegidas
    if args.output:
        # Guardar todo en un archivo único si se especifica --output
        extractor.save_runs_to_file(all_runs_data, args.output)
    elif args.combined_files:
        # Guardar cada repositorio en un archivo único
        extractor.save_runs_by_repository(all_runs_data, args.output_dir)
    else:
        # Por defecto: guardar cada run individualmente, organizados por repositorio
        extractor.save_runs_individually_by_repository(all_runs_data, args.output_dir)

if __name__ == "__main__":
    main()
