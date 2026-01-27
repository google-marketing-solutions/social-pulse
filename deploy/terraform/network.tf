# Set up VPC network
resource "google_compute_network" "vpc_network" {
  project                 = var.project_id
  name                    = "sp-vpc-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "vpc_subnet" {
  project       = var.project_id
  name          = "sp-vpc-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = "us-central1"
  network       = google_compute_network.vpc_network.self_link
}

resource "google_compute_global_address" "private_ip_alloc" {
  project       = var.project_id
  name          = "sp-cloudsql-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = google_compute_network.vpc_network.self_link
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
  depends_on              = [google_compute_global_address.private_ip_alloc]
}

resource "google_vpc_access_connector" "connector" {
  project       = var.project_id
  name          = "sp-vpc-connector"
  region        = "us-central1"
  ip_cidr_range = "10.8.0.0/28" # A non-overlapping range within your VPC
  network       = google_compute_network.vpc_network.self_link
  min_instances = 2
  max_instances = 10
}
