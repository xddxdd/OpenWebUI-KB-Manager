# kbmanager/app_logic.py

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple

import click

# tqdm is for progress bars, which might be in APIInterface now, so review
from tqdm import tqdm  # Keep tqdm if progress bar logic remains here, otherwise move it.

# NEW: Import the API Interface
from kbmanager.api_interface import KBManagerAPIInterface  # This is the ONLY reference to open_web_ui_client structure
from kbmanager.exceptions import APIError, FileOperationError
from kbmanager.kbignore_parser import KBIgnoreParser

logger = logging.getLogger(__name__)


@dataclass
class SimpleKnowledgeBase:
    id: str
    name: str
    description: Optional[str] = None


class AppLogic:
    # AppLogic now expects an instance of KBManagerAPIInterface
    def __init__(self, api_interface: KBManagerAPIInterface):
        self._api = api_interface  # Rename for clarity

    async def _upload_single_file_with_progress(self, file_path: Path): # Removed FileModelResponse return type hint to avoid direct api_client.models import
        """
        Uploads a single file using the API interface.
        No visible tqdm bar here, only the overall progress bar in upload_directory_to_kb.
        """
        try:
            # Let the API interface handle the internal progress bar if it has one.
            # Otherwise, this will just call the API directly.
            uploaded_file = await self._api.upload_single_file_with_progress(file_path)
            return uploaded_file
        except APIError as e:
            # Re-raise API errors, AppLogic will catch and report them
            raise
        except Exception as e:
            # Catch unexpected errors during upload
            logging.error(f"An unexpected error occurred during upload for {file_path.name}: {e}")
            raise

    async def create_knowledge_base(self, name: str, description: Optional[str] = None) -> SimpleKnowledgeBase:
        logger.info(f"Attempting to create knowledge base: {name}")
        kb_full_response = await self._api.create_knowledge_base(name, description)
        kb_info = SimpleKnowledgeBase(
            id=kb_full_response.id, name=kb_full_response.name, description=kb_full_response.description
        )
        logger.info(f"Knowledge base '{kb_info.name}' created with ID: {kb_info.id}")
        return kb_info

    async def list_knowledge_bases(self) -> List[SimpleKnowledgeBase]:
        logger.info("Attempting to list knowledge bases.")
        raw_kbs_data = await self._api.list_knowledge_bases()

        kbs: List[SimpleKnowledgeBase] = []
        for kb_data in raw_kbs_data:
            kb_id = kb_data.get("id")
            kb_name = kb_data.get("name")
            kb_description = kb_data.get("description")

            if kb_id and kb_name:
                kbs.append(SimpleKnowledgeBase(id=kb_id, name=kb_name, description=kb_description))
            else:
                logger.warning(f"Skipping KB entry due to missing ID or Name: {kb_data}")

        logger.info(f"Found {len(kbs)} knowledge bases.")
        return kbs

    async def upload_file_to_kb(self, file_path_str: str, kb_id: str):
        file_path = Path(file_path_str)
        if not file_path.is_file():
            raise FileOperationError(f"File not found: {file_path_str}")

        logger.info(f"Starting upload for single file {file_path.name} to knowledge base {kb_id}")

        try:
            uploaded_file = await self._upload_single_file_with_progress(file_path)

            # Use the model exposed by api_interface
            file_ids_for_batch_add = [self._api.KnowledgeFileIdForm(file_id=uploaded_file.id)]

            await self._api.add_files_to_knowledge_base_batch(kb_id, [uploaded_file.id])

            click.echo(f"Successfully uploaded '{file_path.name}' (ID: {uploaded_file.id}) and added to KB '{kb_id}'.")
        except (APIError, FileOperationError) as e:
            logger.error(f"Could not complete file upload and linking: {e}")
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    async def upload_directory_to_kb(self, directory_path_str: str, kb_id: str, ignore_file_path: Optional[str] = None, skip_existing: Optional[bool] = None):
        directory_path = Path(directory_path_str)
        if not directory_path.is_dir():
            raise FileOperationError(f"Directory not found: {directory_path_str}")

        click.echo(f"Scanning directory {directory_path} for upload to KB {kb_id}.")

        kbignore_parser = KBIgnoreParser()
        if ignore_file_path:
            kbignore_parser.load_patterns(Path(ignore_file_path))
        else:
            default_kbignore = directory_path / ".kbignore"
            if default_kbignore.is_file():
                kbignore_parser.load_patterns(default_kbignore)
            else:
                logging.debug(f"No .kbignore file found in {directory_path}, proceeding without ignore rules.")

        files_to_upload: List[Tuple[Path, str]] = []

        if skip_existing:
            existing_files = [
                f.meta.additional_properties["name"]
                for f in await self._api.list_files_for_knowledge_base(kb_id)
                if (
                    hasattr(f, "meta")
                    and isinstance(f.meta, self._api.FileMetadataResponseMeta)
                    and "name" in f.meta.additional_properties
                )
            ]
        else:
            existing_files = []

        for root, _, files_in_dir in os.walk(directory_path):
            current_dir_path = Path(root)
            for file_name in files_in_dir:  # Renamed 'files' to 'files_in_dir' to avoid conflict with outer 'files_to_upload'
                full_file_path = current_dir_path / file_name
                relative_file_path = str(full_file_path.relative_to(directory_path))

                if file_name in existing_files:
                    logging.debug(f"Skipping existing file: {relative_file_path}")
                    continue

                if not kbignore_parser.is_ignored(str(relative_file_path)):
                    files_to_upload.append((full_file_path, relative_file_path))
                else:
                    logging.debug(f"Skipping ignored file: {relative_file_path}")

        if not files_to_upload:
            click.echo(f"No files found in '{directory_path}' after applying ignore rules. Nothing to upload.")
            return

        click.echo(f"Identified {len(files_to_upload)} files for upload from '{directory_path}'.")

        successful_uploads = 0
        failed_uploads = 0
        uploaded_file_ids_for_batch: List[str] = []

        # Create a list of tasks. Each task is associated with its original file path/name.
        # This is more robust than a dictionary mapping the task object itself.
        tasks_with_info = []
        for full_path, _ in files_to_upload:
            task = asyncio.create_task(self._upload_single_file_with_progress(full_path))
            tasks_with_info.append((task, full_path.name))  # Store task and original filename

        # Extract just the task objects for as_completed
        tasks_only = [task for task, _ in tasks_with_info]

        with tqdm(total=len(files_to_upload), desc="Overall Upload Progress", unit="file", ncols=100) as overall_pbar:
            for future in asyncio.as_completed(tasks_only):  # Iterate over future objects yielded by as_completed
                # To get the original file name, we need to find which task this future corresponds to.
                # A more efficient approach for large numbers of files would be to map future-to-filename
                # after tasks are already created, but for typical CLI use, this is usually fine.
                # The safest way is to avoid the dictionary lookup on 'future' directly.

                original_file_name_for_logging = "Unknown File"  # Fallback
                try:
                    # Find the original filename associated with this completed future/task object
                    # This lookup is what was failing before.
                    # Instead, we should extract the filename from the already 'await'ed uploaded_file or pass it.

                    # The `_upload_single_file_with_progress` already returns the `uploaded_file` object
                    # which contains `uploaded_file.filename`. So we don't need to map `future` to `file_name` here.
                    uploaded_file = await future  # Await the future to get the result from the async function

                    uploaded_file_ids_for_batch.append(uploaded_file.id)
                    successful_uploads += 1
                    tqdm.write(f"  -> Uploaded '{uploaded_file.filename}' (ID: {uploaded_file.id})")
                except (APIError) as e:  # Catch APIError specifically
                    failed_uploads += 1
                    # If this error occurred in _upload_single_file_with_progress, it already logs the original file name
                    # But for tqdm.write, we can get it from 'future' if needed, though it's less direct.
                    # Best: Ensure _upload_single_file_with_progress also returns the original file path on error
                    # or passes it as part of the exception if you want to be super precise here.
                    # For now, we'll try to find the filename from the future/task object if it was stored.
                    # This part is tricky because the future itself doesn't directly hold the original filename in
                    # a reliably accessible way after being awaited (or failed).

                    # Simpler approach: when we create task, we pass the filename:
                    # e.g., task = asyncio.create_task(self._upload_single_file_with_progress(full_path, full_path.name))
                    # But the _upload_single_file_with_progress signature doesn't take file_name explicitly.
                    # Let's revert to a slightly simpler task creation that maps task to filename in a dictionary
                    # directly. But use `str(future)` as key, or better, `id(future)` or `hash(future)`.

                    # A more robust way to associate metadata with tasks is using functools.partial or
                    # by extending the Task object (less common).
                    # For now, let's assume the error message contains enough context or
                    # we can find `file_name` from loop over `tasks_with_info`.

                    # A quick, potentially less efficient, but *working* way to map the future back to its filename
                    # This iterates over `tasks_with_info` to find the matching task.
                    associated_filename = "N/A"
                    for t, name in tasks_with_info:
                        if t is future:  # `is` comparison for identity of the task object
                            associated_filename = name
                            break
                    tqdm.write(f"  -> Error uploading '{associated_filename}': {e}")
                    logging.error(f"Failed to upload '{associated_filename}': {e}")
                except Exception as e:  # Catch any other unexpected exceptions
                    failed_uploads += 1
                    associated_filename = "N/A"
                    for t, name in tasks_with_info:
                        if t is future:
                            associated_filename = name
                            break
                    tqdm.write(f"  -> Unexpected error for '{associated_filename}': {e}")
                    logging.error(f"Unexpected error for '{associated_filename}': {e}")
                finally:
                    overall_pbar.update(1)  # Always update the overall progress bar

        click.echo(f"\nUpload summary:")
        click.echo(f"  - Successfully uploaded: {successful_uploads} files")
        if failed_uploads > 0:
            click.echo(click.style(f"  - Failed to upload: {failed_uploads} files", fg='red'))

        if successful_uploads == 0:  # Check if any files were uploaded successfully
            click.echo("No files were successfully uploaded. Linking to KB skipped.")
            return

        click.echo(
            f"Linking {len(uploaded_file_ids_for_batch)} successfully uploaded files to Knowledge Base '{kb_id}'...")
        try:
            await self._api.add_files_to_knowledge_base_batch(kb_id, uploaded_file_ids_for_batch)

            click.echo(f"Successfully linked {len(uploaded_file_ids_for_batch)} files to KB '{kb_id}'.")
        except APIError as e:
            logging.error(f"Failed to link files to KB {kb_id}: {e}")
            click.echo(f"Error linking files to KB: {e}", err=True)
            sys.exit(1)  # Exit if linking fails

    async def update_file_content(self, file_id: str, new_file_path_str: str):
        new_file_path = Path(new_file_path_str)
        if not new_file_path.is_file():
            raise FileOperationError(f"New content file not found: {new_file_path_str}")

        logger.info(f"Updating content for file ID {file_id} from {new_file_path.name}")
        try:
            updated_file = await self._api.update_file_content_by_id(file_id, new_file_path)
            click.echo(f"Successfully updated content for '{updated_file.filename}' (ID: {updated_file.id}).")
        except (APIError, FileOperationError) as e:
            logger.error(f"Failed to update file content for ID {file_id}: {e}")
            click.echo(f"Error updating file content: {e}", err=True)
            sys.exit(1)

    async def delete_file(self, file_id: str):
        logger.info(f"Attempting to delete file ID: {file_id}")
        try:
            await self._api.delete_file_by_id(file_id)
            click.echo(f"Successfully deleted file with ID: {file_id}.")
        except APIError as e:
            logger.error(f"Could not delete file: {e}")
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    async def delete_all_files_from_kb(self, kb_id: str):
        """
        Deletes all files associated with a given knowledge base ID.
        Careful: This performs a list followed by individual deletes.
        """
        # First, list all files in the KB
        click.echo(f"Listing files in Knowledge Base '{kb_id}' to prepare for deletion...")
        try:
            files_to_delete = await self._api.list_files_for_knowledge_base(kb_id)
        except APIError as e:
            raise FileOperationError(f"Failed to list files for deletion: {e}")

        if not files_to_delete:
            click.echo(f"No files found in Knowledge Base '{kb_id}'. Nothing to delete.")
            return

        click.echo(f"Found {len(files_to_delete)} files in Knowledge Base '{kb_id}'. Starting deletion...")

        delete_tasks = []
        for file in files_to_delete:
            delete_tasks.append(self._api.delete_file_by_id(file.id))

        successful_deletes = 0
        failed_deletes = 0

        # Use tqdm for a progress bar for the deletions
        with tqdm(total=len(delete_tasks), desc="Deleting Files", unit="file", ncols=100) as pbar:
            for task in asyncio.as_completed(delete_tasks):
                try:
                    await task
                    successful_deletes += 1
                except APIError as e:
                    logger.error(f"Failed to delete a file during batch deletion: {e}")
                    failed_deletes += 1
                finally:
                    pbar.update(1)

        click.echo(f"\nDeletion summary for Knowledge Base '{kb_id}':")
        click.echo(f"  - Successfully deleted: {successful_deletes}")
        if failed_deletes > 0:
            click.echo(click.style(f"  - Failed to delete: {failed_deletes}", fg='red'))
            raise FileOperationError(f"Completed with {failed_deletes} errors during deletion.")
        else:
            click.echo(click.style("  - All files deleted successfully.", fg='green'))


    async def list_files(self, kb_id: str, search_query: Optional[str] = None) -> List[Any]:  # Use Any for return type
        """Lists files for a specific knowledge base, optionally filtered by a search query."""
        logger.info(f"Attempting to list files for KB ID: '{kb_id}', search query: '{search_query or 'None'}'")
        try:
            files = await self._api.list_files_for_knowledge_base(kb_id)

            # Apply client-side search (requires FileMetadataResponseMeta from api_interface)
            if search_query:
                logger.info(f"Applying client-side search for '{search_query}' to {len(files)} files.")
                files = [
                    f
                    for f in files
                    if (
                        hasattr(f, "meta")
                        and isinstance(f.meta, self._api.FileMetadataResponseMeta)
                        and "name" in f.meta.additional_properties
                        and search_query.lower() in str(f.meta.additional_properties["name"]).lower()
                    )
                ]

            return files
        except APIError as e:
            logger.error(f"Could not list files for KB '{kb_id}': {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing KB files for '{kb_id}': {e}", exc_info=True)
            raise
