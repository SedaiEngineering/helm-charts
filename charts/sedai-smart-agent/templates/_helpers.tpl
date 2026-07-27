{{/*
Expand the name of the chart.
*/}}
{{- define "sedai-smart-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "sedai-smart-agent.fullname" -}}
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
{{- define "sedai-smart-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sedai-smart-agent.labels" -}}
helm.sh/chart: {{ include "sedai-smart-agent.chart" . }}
{{ include "sedai-smart-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sedai-smart-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sedai-smart-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "sedai-smart-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "sedai-smart-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Global annotations
*/}}
{{- define "sedai-smart-agent.globalAnnotations" -}}
{{- with .Values.globalAnnotations }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Image repository helper - constructs full image URI
Usage: {{ include "sedai-smart-agent.imageRepository" (dict "globalRegistry" .Values.globalRegistry "repository" .Values.image.smartAgent.repository) }}
*/}}
{{- define "sedai-smart-agent.imageRepository" -}}
{{- if and .globalRegistry (not (or (contains "." .repository) (contains ":" .repository))) -}}
{{- printf "%s/%s" .globalRegistry .repository -}}
{{- else -}}
{{- .repository -}}
{{- end -}}
{{- end -}}

{{/*
Resolves the spec-controller store driver, honouring the "pgx for new installs, existing
customers flip manually" policy:
  1. If sedaiSync.dbDriver is set explicitly, it always wins (the manual flip; also the escape hatch).
  2. Else, if the controller Deployment already exists, PRESERVE its current driver — so an existing
     SQLite customer is never auto-migrated on a `helm upgrade`; they stay put until they set
     dbDriver=pgx themselves.
  3. Else (brand-new install, no existing Deployment) default to "pgx" — greenfield goes straight to
     the shared Postgres.
Note: `lookup` returns empty during `helm template`/`--dry-run`, so previews render "pgx"; the
real install/upgrade path resolves correctly.
*/}}
{{- define "sedai-smart-agent.specControllerDriver" -}}
{{- if .Values.sedaiSync.dbDriver -}}
{{- .Values.sedaiSync.dbDriver -}}
{{- else -}}
{{- $dep := lookup "apps/v1" "Deployment" .Release.Namespace "sedai-kube-spec-controller" -}}
{{- if $dep -}}
{{- $driver := "sqlite3" -}}
{{- range $c := $dep.spec.template.spec.containers -}}
{{- if eq $c.name "sedai-kube-spec-controller" -}}
{{- range $e := $c.env -}}
{{- if eq $e.name "SEDAI_KUBE_SPEC_CONTROLLER_DB_DRIVER_NAME" -}}
{{- $driver = $e.value -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- $driver -}}
{{- else -}}
pgx
{{- end -}}
{{- end -}}
{{- end -}}
