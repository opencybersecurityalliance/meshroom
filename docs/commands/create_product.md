# meshroom create product

!!! Usage
    **meshroom create product** [OPTIONS] NAME

Scaffold a new Product, optionally from a template found under `templates/`, into `products/<NAME>` folder.
If no template is passed the produce is created empty. If a template is passed the template is interpolated to the product's directory

### Options

option | description
--- | ---
  --from TEMPLATE |  Path to a `templates/` subdirectory to scaffold the product from
