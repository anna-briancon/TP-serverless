# TP1 - Serverless & Object Storage : Azure Functions vs AWS Lambda

## Objectif

Ce projet compare deux architectures **serverless** exécutées **en local** autour du même cas d'usage :  
déposer un fichier dans un object storage, déclencher automatiquement un traitement, puis stocker un résultat.

- **Azure** : Azure Functions + Azurite
- **AWS** : Lambda + LocalStack

---

## Architecture mise en place

### Schéma global

```text
AZURE
HTTP Trigger
   ↓
Blob Storage (Azurite)
   ↓
Blob Trigger
   ↓
Table Storage (Azurite)

AWS
Lambda upload (invocation CLI)
   ↓
S3 (LocalStack)
   ↓
S3 Event Notification
   ↓
Lambda process
   ↓
DynamoDB (LocalStack)
```

### Structure du dépôt

```text
.
├── azure/
│   └── projet Azure Functions
├── aws/
│   ├── upload_function/
│   ├── process_function/
│   ├── localstack/
│   └── scripts/
└── README.md
```

---

## Rôle des fonctions

### Partie Azure

#### 1. Fonction HTTP Trigger

Cette fonction reçoit une requête HTTP contenant un JSON du type :

```json
{
  "name": "test.txt",
  "content": "Hello serverless"
}
```

Elle crée ensuite un fichier dans le Blob Storage local via Azurite.

#### 2. Fonction Blob Trigger

Cette fonction est déclenchée automatiquement lorsqu'un nouveau blob est ajouté dans le container surveillé.

Elle :

- lit le contenu du blob,
- récupère quelques informations utiles,
- écrit un enregistrement dans Table Storage :
  - nom du fichier,
  - date de traitement,
  - taille,
  - aperçu du contenu.

### Partie AWS

#### 1. Lambda d'upload

Cette fonction reçoit un événement JSON et écrit un objet dans un bucket S3 local sur LocalStack.

Exemple d'entrée :

```json
{
  "name": "test.txt",
  "content": "Hello serverless"
}
```

#### 2. Lambda de traitement

Cette fonction est déclenchée automatiquement par une notification S3 sur l'événement `s3:ObjectCreated:*`.

Elle :

- lit l'objet créé dans S3,
- extrait quelques informations,
- écrit un enregistrement dans DynamoDB :
  - identifiant,
  - nom du fichier,
  - date,
  - taille,
  - aperçu du contenu.

---

## Lancement en local

### Partie A – Azure Functions + Azurite

#### Pré-requis

- Python
- Azure Functions Core Tools
- Azurite
- VS Code conseillé

#### Démarrage

Dans un terminal :

```bash
cd azure
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Lancer Azurite dans un autre terminal :

```bash
azurite --location .azurite --debug .azurite/debug.log
```

![Azure lancement](/screenshots/img_azure/Azurite_lance.png)

Lancer les fonctions Azure :

```bash
func start
```
![Azure function](/screenshots/img_azure/Azure_Functions.png)

#### Test

Dans un autre terminal :

```bash
curl -X POST http://localhost:7071/api/upload \
  -H "Content-Type: application/json" \
  -d '{"name":"test.txt","content":"Hello serverless depuis Azure"}'
```
![Http trigger](/screenshots/img_azure/HTTP_trigger.png)


#### Vérification attendue

- le blob est créé dans Azurite,
- la fonction Blob Trigger s'exécute,
- une ligne est ajoutée dans Table Storage.

![Verif azure](/screenshots/img_azure/Logs_execution.png)


### Partie B - AWS Lambda + LocalStack

#### Pré-requis

- Docker
- LocalStack
- AWS CLI
- Python

#### Configuration AWS CLI

```bash
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set default.region eu-west-1
```

#### Démarrage de LocalStack

```bash
cd aws/localstack
docker compose up -d
```

#### Création des ressources et packaging

Depuis la racine du projet :

```bash
./aws/scripts/package-lambdas.sh
./aws/scripts/create-resources.sh
```

#### Test

```bash
./aws/scripts/test.sh
```

Ou invocation manuelle :

```bash
aws --endpoint-url=http://localhost:4566 lambda invoke \
  --function-name upload-function \
  --payload '{"name":"test.txt","content":"Hello serverless depuis AWS"}' \
  output.json
```

#### Vérification attendue

Vérifier le bucket S3 :

```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://mon-bucket-tp/
```
![Bucket S3](/screenshots/img_aws/bucket_S3.png)

Vérifier DynamoDB :

```bash
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name tp-results
```
![DynamoDB](/screenshots/img_aws/DynamoDB.png)

---

## Analyse comparative

### 1. Modèle de triggers

- **Azure** repose sur un modèle très intégré au runtime : les triggers et bindings sont déclarés directement dans l'application. Le lien entre la fonction et le stockage est donc assez simple à mettre en place.

- **AWS** demande une configuration plus explicite : la Lambda existe séparément, puis il faut configurer la notification S3 et l'autorisation d'invocation.

**Conclusion :**

- Azure : plus déclaratif
- AWS : plus explicite et plus proche de l'infrastructure réelle

### 2. Developer Experience

- **Azure** est rapide à prendre en main sur ce TP :
  - peu de configuration,
  - lancement simple avec `func start`,
  - Azurite est léger,
  - logs faciles à lire.

- **AWS** avec LocalStack demande plus d'étapes :
  - Docker,
  - création manuelle des ressources,
  - packaging des Lambdas,
  - configuration du trigger S3.

**Conclusion :**

- Azure est plus fluide pour débuter
- AWS demande plus de manipulation mais montre mieux le fonctionnement réel des services

### 3. Configuration

- **Azure** nécessite moins de boilerplate grâce aux bindings.
- **AWS** demande davantage de commandes CLI et de configuration explicite.

**Conclusion :**

- Azure : configuration plus compacte
- AWS : configuration plus détaillée et plus verbeuse

### 4. Émulateurs locaux

- **Azurite** est simple à lancer et suffit pour ce TP. Il couvre bien Blob Storage et Table Storage en local.

- **LocalStack** est plus lourd, mais il permet d'émuler plusieurs services AWS dans une même architecture.

**Conclusion :**

- Azurite : simple et ciblé
- LocalStack : plus complet mais plus complexe

### 5. Portabilité

La logique métier reste portable :

- lire un fichier,
- calculer sa taille,
- extraire un aperçu,
- enregistrer un résultat.

En revanche, les triggers, SDK et configurations restent très liés au provider.

**Conclusion :**

- la logique métier peut être réutilisée,
- l'intégration serverless et storage dépend fortement de la plateforme choisie.

---

## Bilan

Ce TP montre que les deux plateformes permettent de construire la même logique événementielle en local, mais avec des approches différentes :

- **Azure** privilégie une expérience développeur plus simple et plus intégrée.
- **AWS** expose davantage la logique d'assemblage des services.

Le résultat obtenu est fonctionnel sur les deux environnements :

- **Azure** : HTTP → Blob → Table
- **AWS** : Lambda → S3 → DynamoDB
