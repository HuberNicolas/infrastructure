# SDG Tag Heroes: data on the server

The stack starts with empty databases. The dataset is built on a workstation (dummy dataset or the thesis data, see
the [SDG Tag Heroes README](https://github.com/HuberNicolas/sdg-tag-heroes#quick-start)) and then copied to the
server once. Afterwards the server keeps its own state (users, votes, XP); it is not overwritten on deployments.

> [!IMPORTANT]
> Decide first which dataset goes online. The thesis dataset contains titles and abstracts of ZORA publications; the
> [dummy dataset](https://github.com/HuberNicolas/sdg-tag-heroes#dummy-dataset) is safe to publish. Set
> `PREDICTION_MODEL` and `MAP_PARTITIONS` in Coolify to match (Aurora/1000 or Dvdblk/3).

All commands below run from the `sdg-tag-heroes` repository on the workstation, with its local stack running.

## 1. Export on the workstation

```bash
mkdir -p transfer
```

```bash
source env/mariadb.env && docker exec mariadb-database mariadb-dump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction igcl | gzip > transfer/igcl.sql.gz
```

```bash
source env/mongodb.env && docker exec mongodb-database mongodump -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --db sdg_database --archive --gzip > transfer/sdg_database.archive.gz
```

```bash
curl -s -X POST http://localhost:2003/collections/publications-mt/snapshots | tee transfer/snapshot.json
```

```bash
curl -s -o transfer/publications-mt.snapshot "http://localhost:2003/collections/publications-mt/snapshots/$(jq -r .result.name transfer/snapshot.json)"
```

The UMAP models are files, not database content:

```bash
tar -czf transfer/umap_model.tar.gz -C data/api umap_model
```

## 2. Copy to the server

```bash
rsync -avP transfer/ root@<server-ip>:/root/transfer/
```

## 3. Import on the server

Coolify names containers `<service>-<resource-uuid>`. Log in and look them up once:

```bash
ssh root@<server-ip>
```

```bash
API=$(docker ps -qf name=^api-) MARIADB=$(docker ps -qf name=^mariadb-) MONGODB=$(docker ps -qf name=^mongodb-) QDRANT=$(docker ps -qf name=^qdrant-)
```

MariaDB and MongoDB (the passwords are the generated `SERVICE_PASSWORD_*` values, visible in Coolify):

```bash
gunzip -c transfer/igcl.sql.gz | docker exec -i $MARIADB sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" igcl'
```

```bash
docker exec -i $MONGODB sh -c 'mongorestore -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip --drop' < transfer/sdg_database.archive.gz
```

Qdrant has no curl in its image, so a throwaway curl container joins the stack network:

```bash
docker run --rm --network container:$QDRANT -v /root/transfer:/transfer curlimages/curl -sf -X POST "http://localhost:6333/collections/publications-mt/snapshots/upload?priority=snapshot" -F snapshot=@/transfer/publications-mt.snapshot
```

UMAP models into the API volume, then restart the API so it loads them:

```bash
tar -xzf transfer/umap_model.tar.gz -C /tmp && docker cp /tmp/umap_model $API:/data/api/ && docker restart $API
```

```bash
rm -rf /root/transfer /tmp/umap_model
```

## 4. Check

- `https://sdg-tag-heroes-api.<domain>/docs` loads, `GET /sdgs` answers after logging in
- Log in on `https://sdg-tag-heroes.<domain>` and open the exploration map
- **Change the passwords of the accounts from `users.env`**; the dump contains them with their workstation values

## Backups

The whole server is backed up daily by Hetzner (7 days). For a logical backup of the game state, repeat the export
commands of step 1 on the server (with the container variables of step 3) and copy the files off the server.
