package main

import (
	"log"
	"os"

	"github.com/spf13/cobra"
	"k8s.io/component-base/cli"
)

func main() {
	command := newCommand()

	f, err := os.OpenFile("testlogfile", os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalf("error opening file: %v", err)
	}
	defer f.Close()

	log.SetOutput(f)
	log.Println("This is a test log entry for microshift (A).")

	code := cli.Run(command)
	os.Exit(code)
}

func newCommand() *cobra.Command {
	opt := configGenOpts{}

	cmd := &cobra.Command{
		Use:   "generate-config",
		Short: "use openapiv3 schemas in CRDs format to generate yaml or embed in files",
		RunE: func(cmd *cobra.Command, args []string) error {
			if err := opt.Options(); err != nil {
				return err
			}
			return opt.Run()
		},
	}
	opt.BindFlags(cmd.Flags())

	return cmd
}
