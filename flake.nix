{
  description = "u4u-engine development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python312;
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          (python.withPackages (ps: with ps; [
            # Testing
            pytest
            responses
            requests
            tenacity

            # Auth
            bcrypt

            # Utilities
            urllib3

            # Database
            psycopg2
            # Async stack for the HealthKit ingestion datastore (engine/health).
            # api.py imports engine.health.api at module load, so these must be
            # present for the test suite to import under `nix develop`.
            sqlalchemy
            asyncpg

            # API surface (required by api.py and engine/users/deps.py;
            # the in-process test suite doesn't spin up uvicorn but does
            # import these modules)
            fastapi
            pydantic
            python-multipart
            # httpx backs starlette's TestClient; without it the FastAPI
            # endpoint tests (e.g. tracking/test_api.py) importorskip and
            # silently skip locally. Pinning it here gives local/CI parity.
            httpx
          ]))
          pkgs.nodejs_20
          # Linter (standalone Rust binary, not a python package). Config in pyproject.toml.
          pkgs.ruff
        ];

        shellHook = ''
          echo "u4u-engine dev shell ready"
          echo "Python: $(python --version)"
        '';
      };
    };
}
