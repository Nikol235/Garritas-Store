import { Routes } from "@angular/router";
import { adminGuard, authGuard, clienteGuard } from "./core/guards";

export const routes: Routes = [
  { path: "", pathMatch: "full", redirectTo: "catalogo" },

  // ── Tienda (pública) ──────────────────────────────────────────────
  {
    path: "catalogo",
    title: "Catálogo · Garritas Store",
    loadComponent: () => import("./pages/catalogo.page").then((m) => m.CatalogoPage),
  },
  {
    path: "nueva-orden",
    title: "Nueva orden · Garritas Store",
    canActivate: [clienteGuard],
    loadComponent: () => import("./pages/nueva-orden.page").then((m) => m.NuevaOrdenPage),
  },
  {
    path: "carrito",
    title: "Carrito · Garritas Store",
    canActivate: [clienteGuard],
    loadComponent: () => import("./pages/carrito.page").then((m) => m.CarritoPage),
  },
  {
    path: "sedes",
    title: "Sedes · Garritas Store",
    loadComponent: () => import("./pages/sedes.page").then((m) => m.SedesPage),
  },
  {
    path: "especialistas",
    title: "Especialistas · Garritas Store",
    loadComponent: () => import("./pages/especialistas.page").then((m) => m.EspecialistasPage),
  },
  {
    path: "prestaciones",
    title: "Servicios por sede · Garritas Store",
    loadComponent: () => import("./pages/prestaciones.page").then((m) => m.PrestacionesPage),
  },

  // ── Mi espacio (requiere sesión) ──────────────────────────────────
  {
    path: "",
    canActivateChild: [authGuard],
    children: [
      {
        // También es la URL de retorno de Mercado Pago (/compras?venta_id=...)
        path: "compras",
        title: "Compras · Garritas Store",
        loadComponent: () => import("./pages/compras.page").then((m) => m.ComprasPage),
      },
      {
        path: "planes",
        title: "Planes · Garritas Store",
        loadComponent: () => import("./pages/planes.page").then((m) => m.PlanesPage),
      },
      {
        path: "cuenta",
        title: "Mi cuenta · Garritas Store",
        loadComponent: () => import("./pages/cuenta.page").then((m) => m.CuentaPage),
      },
      {
        path: "citas",
        title: "Citas · Garritas Store",
        loadComponent: () => import("./pages/citas.page").then((m) => m.CitasPage),
      },
      {
        // /envios?initialVenta=123 preselecciona una venta (withComponentInputBinding)
        path: "envios",
        title: "Envíos · Garritas Store",
        loadComponent: () =>
          import("./features/envios/envios.component").then((m) => m.EnviosComponent),
      },
      {
        path: "pagos",
        title: "Pagos · Garritas Store",
        loadComponent: () =>
          import("./features/pagos/pagos.component").then((m) => m.PagosComponent),
      },
    ],
  },

  // ── Administración (rol ADMIN) ────────────────────────────────────
  {
    path: "admin",
    canActivateChild: [authGuard, adminGuard],
    children: [
      { path: "", pathMatch: "full", redirectTo: "productos" },
      {
        path: "logistica",
        title: "Logística · Garritas Store",
        loadComponent: () =>
          import("./features/logistica/logistica.component").then((m) => m.LogisticaComponent),
      },
      {
        path: "productos",
        title: "Productos · Garritas Store",
        loadComponent: () =>
          import("./features/admin/productos.component").then((m) => m.ProductosComponent),
      },
      {
        path: "categorias",
        title: "Categorías · Garritas Store",
        loadComponent: () => import("./pages/categorias.page").then((m) => m.CategoriasPage),
      },
      {
        path: "clientes",
        title: "Clientes · Garritas Store",
        loadComponent: () =>
          import("./features/admin/clientes.component").then((m) => m.ClientesComponent),
      },
      {
        path: "roles",
        title: "Roles de personal · Garritas Store",
        loadComponent: () =>
          import("./features/admin/roles.component").then((m) => m.RolesComponent),
      },
      {
        path: "usuarios-roles",
        title: "Usuarios y roles · Garritas Store",
        loadComponent: () =>
          import("./features/admin/usuarios-roles.component").then(
            (m) => m.UsuariosRolesComponent,
          ),
      },
    ],
  },

  { path: "**", redirectTo: "catalogo" },
];
