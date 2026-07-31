export type ComponentStatus = 'up' | 'down'

export interface HealthCheck {
  status: ComponentStatus
  message: string
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready'
  service: string
  version: string
  checks: {
    database: HealthCheck
    redis: HealthCheck
  }
  timestamp: string
}
