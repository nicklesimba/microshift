package config

type MultusConfig struct {
	// Valid values are: "true", "false".
	// Defaults to "false".
	// +kubebuilder:default="false"
	Enabled bool `json:"enabled"`
}
