"""Ferramentas de liña de comandos.

Crear a primeira invitación de admin (só se fai unha vez, no servidor):
    python -m app.cli invite --email ismael@example.com --name "Ismael Gil" --admin --coach
"""
import argparse
import asyncio
from types import SimpleNamespace

from app.core.db import SessionLocal, engine
from app.domains.accounts.auth.management import AuthManagement
from app.domains.accounts.auth.repository import AuthRepository
from app.domains.accounts.invitations.management import InvitationManagement
from app.domains.accounts.invitations.repository import InvitationRepository


async def invite(args) -> None:
    async with SessionLocal() as db:
        mgmt = InvitationManagement(InvitationRepository(db), AuthManagement(AuthRepository(db)))
        data = SimpleNamespace(
            email=args.email.lower().strip(), invited_name=args.name, kind="member", minor_name=None,
            is_athlete=not args.no_athlete, grant_admin=args.admin, grant_coach=args.coach, lang=args.lang,
        )
        row = await mgmt.create(data, created_by=None)
        print(f"\nInvitación para {row['invited_name']} <{row['email']}>, caduca {row['expires_at']} UTC")
        print(f"\n  {row['link']}\n")
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("invite", help="Crear unha invitación (útil para o primeiro admin)")
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--admin", action="store_true")
    p.add_argument("--coach", action="store_true")
    p.add_argument("--no-athlete", action="store_true", help="Staff que non compite")
    p.add_argument("--lang", choices=["gl", "es"], default="gl")
    args = parser.parse_args()
    if args.cmd == "invite":
        asyncio.run(invite(args))


if __name__ == "__main__":
    main()
