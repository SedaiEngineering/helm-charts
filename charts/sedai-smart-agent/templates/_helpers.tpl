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
sedai-smart-scheduler helpers — used by templates/sedai-smart-scheduler/*
*/}}
{{- define "smart-scheduler.name" -}}
{{- default "sedai-smart-scheduler" .Values.sedaiSmartScheduler.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "smart-scheduler.fullname" -}}
{{- if .Values.sedaiSmartScheduler.fullnameOverride -}}
{{- .Values.sedaiSmartScheduler.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default "sedai-smart-scheduler" .Values.sedaiSmartScheduler.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "smart-scheduler.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "smart-scheduler.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "smart-scheduler.selectorLabels" -}}
app.kubernetes.io/name: {{ include "smart-scheduler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "smart-scheduler.serviceAccountName" -}}
{{- printf "%s-sa" .Values.workload.smartAgent.name -}}
{{- end -}}

{{- define "smart-scheduler.serviceAccountNamespace" -}}
{{- .Release.Namespace -}}
{{- end -}}

{{- define "smart-scheduler.imageTag" -}}
{{- if .Values.sedaiSmartScheduler.image.tag -}}
{{- .Values.sedaiSmartScheduler.image.tag -}}
{{- else -}}
{{- $minor := .Capabilities.KubeVersion.Minor | replace "+" "" | trimSuffix "*" -}}
{{- $tag := index .Values.sedaiSmartScheduler.image.tagByK8sMinor $minor -}}
{{- required (printf "Unsupported K8s minor 1.%s for scheduler image. Override sedaiSmartScheduler.image.tag or extend sedaiSmartScheduler.image.tagByK8sMinor." $minor) $tag -}}
{{- end -}}
{{- end -}}

{{- define "smart-scheduler.compactorImageTag" -}}
{{- if .Values.sedaiSmartScheduler.compactor.image.tag -}}
{{- .Values.sedaiSmartScheduler.compactor.image.tag -}}
{{- else -}}
{{- $minor := .Capabilities.KubeVersion.Minor | replace "+" "" | trimSuffix "*" -}}
{{- $tag := index .Values.sedaiSmartScheduler.compactor.image.tagByK8sMinor $minor -}}
{{- required (printf "Unsupported K8s minor 1.%s for compactor image. Override sedaiSmartScheduler.compactor.image.tag or extend sedaiSmartScheduler.compactor.image.tagByK8sMinor." $minor) $tag -}}
{{- end -}}
{{- end -}}
