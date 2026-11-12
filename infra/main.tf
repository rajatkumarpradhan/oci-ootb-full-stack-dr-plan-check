# OCI Full Stack Disaster Recovery wiring (template; NOT applied).
#
# OCI Full Stack Disaster Recovery (FSDR) is the built-in OCI service that
# orchestrates switchover/failover of an application stack between regions
# via DR protection groups and DR plans. This template creates the primary
# and standby protection groups, their association, and one switchover plan.
# The local checker in src/ verifies a plan definition covers every member.
#
# This file has NOT been plan/apply validated against a tenancy - it is a
# structural template. Review against the current provider docs before any
# real apply.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCID of the compartment that owns the DR resources"
}

resource "oci_disaster_recovery_dr_protection_group" "primary" {
  compartment_id = var.compartment_ocid
  display_name   = "app-primary-mumbai"
}

resource "oci_disaster_recovery_dr_protection_group" "standby" {
  compartment_id = var.compartment_ocid
  display_name   = "app-standby-hyderabad"
}

resource "oci_disaster_recovery_dr_protection_group_association" "app" {
  from_dr_protection_group_id = oci_disaster_recovery_dr_protection_group.primary.id
  to_dr_protection_group_id   = oci_disaster_recovery_dr_protection_group.standby.id
  role                        = "PRIMARY"
}

# Example member: the database system. Add one members block per protected
# resource; the local checker flags any member left out of the plan steps.
resource "oci_disaster_recovery_dr_protection_group_member" "db" {
  dr_protection_group_id = oci_disaster_recovery_dr_protection_group.primary.id
  member_id              = "ocid1.dbsystem.oc1..example...replace-me"
  member_type            = "DATABASE"
}

resource "oci_disaster_recovery_dr_plan" "switchover" {
  dr_protection_group_id = oci_disaster_recovery_dr_protection_group.standby.id
  display_name           = "app-switchover-to-hyderabad"
  type                   = "SWITCHOVER"
}
