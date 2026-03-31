# Re-test Plan (3 VM)

## 1) Cluster health

```bash
docker node ls
docker stack services nebula
docker stack ps nebula
```

Attendu:
- 1 manager + 2 workers `Ready`
- services répliqués et en `1/1`

## 2) Placement validation

```bash
docker service ps nebula_edge-proxy
docker service ps nebula_users-api
docker service ps nebula_posts-api
docker service ps nebula_feed-api
docker service ps nebula_feed-worker
docker service ps nebula_postgres
docker service ps nebula_redis
```

Attendu:
- `edge-proxy` sur node label `role=edge`
- APIs + worker sur node label `role=app`
- `postgres` + `redis` sur node label `role=data`

## 3) Smoke fonctionnel

```bash
./scripts/test/retest-3vm.sh
```

Attendu:
- création user OK
- création post OK
- post visible dans `/feed/<user_id>`

## 4) Rolling update / rollback

Mettre un nouveau tag d'image sur un service stateless, redeploy, puis vérifier:

```bash
docker service ps nebula_posts-api
docker service logs --tail 50 nebula_posts-api
```

Attendu:
- update `start-first`
- service reste disponible
- rollback possible en cas d'échec
