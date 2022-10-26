import pandas as pd
import psycopg2
import requests
import json
import os

from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from Airflow.plugins.utils.helper import *

load_dotenv()

url = 'https://api.github.com/graphql'
access_token = os.getenv('ACCESS_TOKEN')
headers = {'Content-Type': 'application/json', 'Authorization': f'{access_token}'}

host = os.getenv('POSTGRES_HOST')
username = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')
database = os.getenv('POSTGRES_DB')

conn = psycopg2.connect(
    host=host,
    database=database,
    user=username,
    password=password,
    options="-c search_path=dbo,github_analytics")

cur = conn.cursor()

es_host = os.getenv('ES_HOST')
es_user = os.getenv('ES_USER')
es_pass = os.getenv('ES_PASS')
es_port = os.getenv('ES_PORT')
es = Elasticsearch(f"http://{es_user}:{es_pass}@{es_host}:{es_port}")

path = 'Airflow/dags/github_etl/include/github_queries'


class Task:
    @staticmethod
    def repository():
        repo_list = []
        end_cursor = None
        while True:
            variables = {
                "owner": "Prunedge-Dev-Team",
                "repositories": 100,
                "end_cursor": end_cursor
            }
            query = open(f"{path}/repo.gql").read()
            r = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
            data = r.json()
            page_info = data['data']['repositoryOwner']['repositories']['pageInfo']
            payload = data['data']['repositoryOwner']['repositories']['nodes']
            indices = 4 if not payload else len(payload[0])
            record_size = len(payload)
            payload_to_array(payload, record_size, array=repo_list, indices=indices)
            end_cursor = page_info['endCursor']
            next_page_bool = page_info['hasNextPage']
            if next_page_bool is False:
                break
        df_repo = pd.DataFrame(repo_list)
        df_repo = df_repo.rename(columns={"name": "repoName", "id": "repoId"})
        columns_titles = ["repoId", "repoName", "createdAt", "updatedAt", "isPrivate"]
        df_repo = df_repo.reindex(columns=columns_titles)
        data = json.loads(df_repo.to_json(orient='records'))
        helpers.bulk(es, es_bulk_doc(data, index='repository', id='repoId'))
        pg_insert_repo_table(df_repo, cur, conn)

    @staticmethod
    def user():
        user_list = []
        result_dataframe = pd.read_sql(sql="select reponame from repository limit 1", con=conn)
        repository = result_dataframe.iat[0, 0]
        end_cursor = None
        while True:
            variables = {
                "owner": "Prunedge-Dev-Team",
                "repository": repository,
                "collaborators": 100,
                "end_cursor": end_cursor
            }
            query = open(f"{path}/user.gql").read()
            r = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
            data = r.json()
            page_info = data['data']['repository']['collaborators']['pageInfo']
            payload = data['data']['repository']['collaborators']['nodes']
            indices = 4 if not payload else len(payload[0])
            record_size = len(payload)
            payload_to_array(payload, record_size, array=user_list, indices=indices)
            end_cursor = page_info['endCursor']
            next_page_bool = page_info['hasNextPage']
            if next_page_bool is False:
                break
        df_user = pd.DataFrame(user_list)
        df_user = df_user.rename(columns={"id": "userId", "login": "username"})
        print(df_user)
        data = json.loads(df_user.to_json(orient='records'))
        helpers.bulk(es, es_bulk_doc(data, index='users', id='userId'))
        pg_insert_user_table(df_user, cur, conn)

    @staticmethod
    def branch():
        ref_list = []
        result_dataframe = pd.read_sql(sql="select reponame from repository", con=conn)
        for repository in result_dataframe['reponame'].to_list():
            end_cursor = None
            while True:
                variables = {
                    "owner": "Prunedge-Dev-Team",
                    "repository": repository,
                    "refs": 100,
                    "end_cursor": end_cursor
                }
                query = open(f"{path}/branch.gql").read()
                r = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
                data = r.json()
                page_info = data['data']['repository']['refs']['pageInfo']
                payload = data['data']['repository']['refs']['nodes']
                indices = 2 if not payload else len(payload[0])
                record_size = len(payload)
                payload_to_array_with_repo(payload, record_size, array=ref_list, indices=indices, repository=repository)
                end_cursor = page_info['endCursor']
                next_page_bool = page_info['hasNextPage']
                if next_page_bool is False:
                    break
        df_ref = pd.DataFrame(ref_list)
        df_ref = df_ref.rename(columns={"id": "branchId", "name": "branchName"})
        columns_titles = ["branchId", "branchName", "repoName"]
        df_ref = df_ref.reindex(columns=columns_titles)
        data = json.loads(df_ref.to_json(orient='records'))
        helpers.bulk(es, es_bulk_doc(data, index='branch', id='branchId'))
        pg_insert_branch_table(df_ref, cur, conn)

    @staticmethod
    def pull_request():
        pull_request_list = []
        result_dataframe = pd.read_sql(sql="select reponame from repository", con=conn)
        for repository in result_dataframe['reponame'].to_list():
            end_cursor = None
            while True:
                variables = {
                    "owner": "Prunedge-Dev-Team",
                    "repository": repository,
                    "pull_requests": 100,
                    "end_cursor": end_cursor
                }
                query = open(f"{path}/pull_request.gql").read()
                r = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
                data = r.json()
                page_info = data['data']['repository']['pullRequests']['pageInfo']
                payload = data['data']['repository']['pullRequests']['nodes']
                indices = 16 if not payload else len(payload[0])
                record_size = len(payload)
                payload_to_array_with_repo(payload, record_size, array=pull_request_list, indices=indices,
                                           repository=repository)
                end_cursor = page_info['endCursor']
                next_page_bool = page_info['hasNextPage']
                if next_page_bool is False:
                    break
        df_pull_request = pd.DataFrame(pull_request_list)
        df_pull_request = df_pull_request.rename(columns={"id": "pullRequestId"})
        data = json.loads(df_pull_request.to_json(orient='records'))
        helpers.bulk(es, es_bulk_doc(data, index='pullrequests', id='pullRequestId'))
        pg_insert_pullrequest_table(df_pull_request, cur, conn)

    @staticmethod
    def commit():
        commit_list = []
        result_dataframe = pd.read_sql(sql="select reponame, branchname from branch", con=conn)
        for j in result_dataframe.to_dict('records')[:50]:
            end_cursor = None
            repository = j["reponame"]
            ref = j["branchname"]
            while True:
                variables = {
                    "owner": "Prunedge-Dev-Team",
                    "repository": repository,
                    "ref": ref,
                    "commits": 100,
                    "end_cursor": end_cursor
                }
                query = open(f"{path}/commit.gql").read()
                r = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
                data = r.json()
                page_info = data['data']['repository']['refs']['nodes'][0]['target']['history']['pageInfo']
                payload = data['data']['repository']['refs']['nodes'][0]['target']['history']['nodes']
                record_size = len(payload)
                indices = 7 if not payload else len(payload[0])
                payload_to_array_commit(payload, record_size, array=commit_list, indices=indices, variables=variables)
                end_cursor = page_info['endCursor']
                next_page_bool = page_info['hasNextPage']
                if next_page_bool is False:
                    break
        df_commit = pd.DataFrame(commit_list)
        df_commit = df_commit.rename(columns={"id": "commitId"})
        data = json.loads(df_commit.to_json(orient='records'))
        helpers.bulk(es, es_bulk_doc(data, index='commit', id='commitId'))
        pg_insert_commit_table(df_commit, cur, conn)
