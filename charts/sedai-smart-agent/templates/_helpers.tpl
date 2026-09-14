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
{{- if .Values.workload.smartScheduler.name -}}
{{- .Values.workload.smartScheduler.name | trunc 63 | trimSuffix "-" -}}
{{- else if .Values.sedaiSmartScheduler.fullnameOverride -}}
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

{{- define "smart-scheduler.k8sMinor" -}}
{{- .Capabilities.KubeVersion.Minor | replace "+" "" | trimSuffix "*" -}}
{{- end -}}

{{/*
Scheduler version-skew lookup: exact minor, else N-1 (https://kubernetes.io/releases/version-skew-policy/#kube-apiserver-1). "" if neither is mapped.
*/}}
{{- define "smart-scheduler.resolveTag" -}}
{{- $minor := atoi .minor -}}
{{- $exact := toString $minor -}}
{{- $prior := toString (sub $minor 1) -}}
{{- if hasKey .tagByK8sMinor $exact -}}
{{- index .tagByK8sMinor $exact -}}
{{- else if hasKey .tagByK8sMinor $prior -}}
{{- index .tagByK8sMinor $prior -}}
{{- end -}}
{{- end -}}

{{/*
Compactor lookup: exact minor only, no N-1 (descheduler isn't bound by kube-scheduler's skew policy). "" if unmapped.
*/}}
{{- define "smart-scheduler.resolveTagExact" -}}
{{- $exact := toString (atoi .minor) -}}
{{- if hasKey .tagByK8sMinor $exact -}}
{{- index .tagByK8sMinor $exact -}}
{{- end -}}
{{- end -}}

{{/*
Override, else lookup. May be empty if the cluster's minor is unsupported.
*/}}
{{- define "smart-scheduler.schedulerTagRaw" -}}
{{- if .Values.image.scheduler.imageTag -}}
{{- .Values.image.scheduler.imageTag -}}
{{- else -}}
{{- include "smart-scheduler.resolveTag" (dict "minor" (include "smart-scheduler.k8sMinor" .) "tagByK8sMinor" .Values.image.scheduler.tagByK8sMinor) -}}
{{- end -}}
{{- end -}}

{{- define "smart-scheduler.compactorTagRaw" -}}
{{- if .Values.image.compactor.imageTag -}}
{{- .Values.image.compactor.imageTag -}}
{{- else -}}
{{- include "smart-scheduler.resolveTagExact" (dict "minor" (include "smart-scheduler.k8sMinor" .) "tagByK8sMinor" .Values.image.compactor.tagByK8sMinor) -}}
{{- end -}}
{{- end -}}

{{/*
`required` is a defensive guardrail — templates are already gated on installOk, so this shouldn't trip.
*/}}
{{- define "smart-scheduler.imageTag" -}}
{{- $minor := include "smart-scheduler.k8sMinor" . -}}
{{- required (printf "Unsupported K8s minor 1.%s for scheduler image. Override image.scheduler.imageTag or extend image.scheduler.tagByK8sMinor." $minor) (include "smart-scheduler.schedulerTagRaw" .) -}}
{{- end -}}

{{- define "smart-scheduler.compactorImageTag" -}}
{{- $minor := include "smart-scheduler.k8sMinor" . -}}
{{- required (printf "Unsupported K8s minor 1.%s for compactor image. Override image.compactor.imageTag or extend image.compactor.tagByK8sMinor." $minor) (include "smart-scheduler.compactorTagRaw" .) -}}
{{- end -}}

{{/*
"true" if scheduler is compatible and (compactor is disabled or also compatible) — skips both if either fails.
*/}}
{{- define "smart-scheduler.versionCompatible" -}}
{{- $schedulerOk := ne (include "smart-scheduler.schedulerTagRaw" .) "" -}}
{{- $compactorOk := or (not .Values.sedaiSmartScheduler.compactor.enabled) (ne (include "smart-scheduler.compactorTagRaw" .) "") -}}
{{- if and $schedulerOk $compactorOk -}}true{{- end -}}
{{- end -}}

{{/*
Single flag every sedai-smart-scheduler/* template gates on: enabled AND version-compatible.
*/}}
{{- define "smart-scheduler.installOk" -}}
{{- if and .Values.sedaiSmartScheduler.enabled (eq (include "smart-scheduler.versionCompatible" .) "true") -}}true{{- end -}}
{{- end -}}
