{{/*
Expand the name of the chart.
*/}}
{{- define "sophia.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "sophia.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sophia.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sophia.labels" -}}
helm.sh/chart: {{ include "sophia.chart" . }}
{{ include "sophia.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sophia.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sophia.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "sophia.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "sophia.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the secret to use
*/}}
{{- define "sophia.secretName" -}}
{{- default (printf "%s-secret" (include "sophia.fullname" .)) .Values.secrets.name }}
{{- end }}

{{/*
Create the name of the configmap to use
*/}}
{{- define "sophia.configMapName" -}}
{{- printf "%s-config" (include "sophia.fullname" .) }}
{{- end }}

{{/*
Create ingress hostname
*/}}
{{- define "sophia.ingressHost" -}}
{{- if .Values.ingress.hosts }}
{{- (index .Values.ingress.hosts 0).host }}
{{- else }}
{{- "www.sophia-intel.ai" }}
{{- end }}
{{- end }}

{{/*
Create API URL for frontend
*/}}
{{- define "sophia.apiUrl" -}}
{{- if .Values.ingress.enabled }}
{{- printf "https://%s/api" (include "sophia.ingressHost" .) }}
{{- else }}
{{- printf "http://%s-api:%d" (include "sophia.fullname" .) (.Values.api.service.port | int) }}
{{- end }}
{{- end }}

{{/*
Create database URL with secret reference
*/}}
{{- define "sophia.databaseUrl" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "postgresql://%s:%s@%s-postgresql:5432/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "sophia.fullname" .) .Values.postgresql.auth.database }}
{{- else }}
{{- "$(DATABASE_URL)" }}
{{- end }}
{{- end }}

{{/*
Create Redis URL
*/}}
{{- define "sophia.redisUrl" -}}
{{- if .Values.dependencies.redis.enabled }}
{{- printf "redis://%s-redis:6379/0" (include "sophia.fullname" .) }}
{{- else }}
{{- "$(REDIS_URL)" }}
{{- end }}
{{- end }}

{{/*
Create Qdrant URL
*/}}
{{- define "sophia.qdrantUrl" -}}
{{- if .Values.dependencies.qdrant.enabled }}
{{- printf "http://%s-qdrant:6333" (include "sophia.fullname" .) }}
{{- else }}
{{- "$(QDRANT_URL)" }}
{{- end }}
{{- end }}

