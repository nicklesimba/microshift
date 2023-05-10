package main

import (
	"log"
	"os"

	"github.com/spf13/cobra"

	"k8s.io/cli-runtime/pkg/genericclioptions"
	"k8s.io/component-base/cli"

	cmds "github.com/openshift/microshift/pkg/cmd"
	"github.com/openshift/microshift/pkg/config"
)

func main() {
	command := newCommand()

	f, err := os.OpenFile("testlogfile", os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalf("error opening file: %v", err)
	}
	defer f.Close()

	log.SetOutput(f)
	log.Println("This is a test log entry for microshift (B).")

	code := cli.Run(command)
	os.Exit(code)
}

func newCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "microshift",
		Short: "MicroShift, a minimal OpenShift",
		Run: func(cmd *cobra.Command, args []string) {
			_ = cmd.Help() // err is always nil
			os.Exit(1)
		},
	}
	originalHelpFunc := cmd.HelpFunc()
	cmd.SetHelpFunc(func(command *cobra.Command, strings []string) {
		config.HideUnsupportedFlags(command.Flags())
		originalHelpFunc(command, strings)
	})

	ioStreams := genericclioptions.IOStreams{In: os.Stdin, Out: os.Stdout, ErrOut: os.Stderr}

	cmd.AddCommand(cmds.NewRunMicroshiftCommand())
	cmd.AddCommand(cmds.NewVersionCommand(ioStreams))
	cmd.AddCommand(cmds.NewShowConfigCommand(ioStreams))
	return cmd
}
