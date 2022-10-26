def es_bulk_doc(data, index: str, id: str):
    for document in data:
        yield {
            "_index": index,
            "_id": f"{document[id]}",
            "_source": document
        }

# def pg_insert_repo_table_csv(df, cur, conn):
    #     with open(f'{file_path}/repository.csv', 'r') as file:
    #         cur.copy_expert(
    #             "COPY repository (repoId, repoName, createdAt, updatedAt, isPrivate) values(%s, %s, %s, %s, %s)",
    #             "COPY \"Employees_temp\" FROM STDIN WITH CSV HEADER DELIMITER AS ',' QUOTE '\"'",
    #             file,
    #         )
    #         conn.commit()


def pg_insert_cursor(cursor, table, column, indexed_column, cur, conn, state=1):
    try:
        sql = "INSERT INTO {} ({},{}) VALUES (%s, %s) " \
              "ON CONFLICT ({})" \
              "DO UPDATE SET {} = EXCLUDED.{}"
        cur.execute(sql.format(table, indexed_column, column, indexed_column, column, column), (state, cursor))
        conn.commit()
        print("cursor upserted")
    except Exception as e:
        print(e)


def pg_insert_commits_cursor(cursor, table, column, indexed_column, cur, conn, state: list):
    try:
        sql = "INSERT INTO {} ({},reponame,{}) VALUES (%s, %s, %s) " \
              "ON CONFLICT ({},reponame)" \
              "DO UPDATE SET {} = EXCLUDED.{}"
        cur.execute(sql.format(table, indexed_column, column, indexed_column, column, column), (state[0], state[1], cursor))
        conn.commit()
        print("cursor upserted")
    except Exception as e:
        print(e)


def pg_insert_repo_table(df, cur, conn):
    for index, row in df.iterrows():
        try:
            cur.execute(
                "INSERT INTO github_analytics.repository (repoId, repoName, createdAt, updatedAt, isPrivate) values(%s, %s, %s, %s, %s)",
                (row.repoId, row.repoName, row.createdAt, row.updatedAt, row.isPrivate),
            )
            conn.commit()
        except Exception as e:
            print(e)
            pass


def pg_insert_branch_table(df, cur, conn):
    for index, row in df.iterrows():
        try:
            cur.execute(
                "INSERT INTO github_analytics.branch (branchId, branchName, repoName) values(%s, %s, %s)",
                (row.branchId, row.branchName, row.repoName),
            )
            conn.commit()
        except Exception as e:
            print(e)
            pass


def pg_insert_user_table(df, cur, conn):
    for index, row in df.iterrows():
        try:
            cur.execute(
                "INSERT INTO github_analytics.users (userId, author, email, avatarUrl) values(%s, %s, %s, %s)",
                (row.userId, row.username, row.email, row.avatarUrl),
            )
            conn.commit()
        except Exception as e:
            print(e)
            pass


def pg_insert_pullrequest_table(df, cur, conn):
    for index, row in df.iterrows():
        try:
            cur.execute(
                "INSERT INTO github_analytics.pullrequest (pullRequestId, title, author, createdAt, updatedAt, state, "
                "closed, closedAt,merged, mergedBy, mergedAt, prNumber, reviewDecision, sourceBranchName, "
                "destinationBranchName, repoName) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (row.pullRequestId, row.title, row.author, row.createdAt, row.updatedAt, row.state, row.closed,
                 row.closedAt, row.merged, row.mergedBy, row.mergedAt, row.number, row.reviewDecision,
                 row.headRef, row.baseRef, row.repoName),
            )
            conn.commit()
        except Exception as e:
            print(e)
            pass


def pg_insert_commit_table(df, cur, conn):
    for index, row in df.iterrows():
        try:
            cur.execute(
                "INSERT INTO github_analytics.commits (commitId, author, additions, deletions, changedFiles, message, pushedDate, "
                "authoredDate, committedDate, branchName, repoName) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                row.commitId, row.author, row.additions, row.deletions, row.changedFiles, row.message, row.pushedDate,
                row.authoredDate, row.committedDate, row.branchName, row.repoName),
            )
            conn.commit()
        except Exception as e:
            print(e)
            pass


def payload_to_array(payload, record_size, array, indices):
    for i in range(record_size):
        dictionary = payload[i]
        unpack_nested_dict(dictionary)
        itr = {key: dictionary[key] for key in list(dictionary)[:indices]}
        array.append(itr)


def payload_to_array_with_repo(payload, record_size, array, indices, repository):
    for i in range(record_size):
        dictionary = payload[i]
        unpack_nested_dict(dictionary)
        itr = {key: dictionary[key] for key in list(dictionary)[:indices]}
        itr['repoName'] = repository
        array.append(itr)


def payload_to_array_commit(payload, record_size, array, indices, variables):
    for i in range(record_size):
        dictionary = payload[i]
        unpack_nested_dict(dictionary)
        itr = {key: dictionary[key] for key in list(dictionary)[:indices]}
        itr['branchName'] = variables["ref"]
        itr['repoName'] = variables["repository"]
        array.append(itr)


def unpack_nested_dict(dictionary):
    for key in dictionary:
        if isinstance(dictionary[key], dict):
            first_degree_nest = list(dictionary[key].values())[0]
            dictionary[key] = first_degree_nest
            if isinstance(first_degree_nest, dict):
                second_degree_nest = list(first_degree_nest.values())[0]
                dictionary[key] = second_degree_nest
    return dictionary[key]
