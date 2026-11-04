import { Button, HStack, IconButton, Input, Stack, Text } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRef, useState } from "react"
import { LuDownload, LuFileText, LuTrash2, LuUpload } from "react-icons/lu"
import {
  documentsDeleteDocumentMutation,
  documentsListDocumentsOptions,
  documentsUploadDocumentMutation,
} from "@/client/@tanstack/react-query.gen"
import type { DocumentRead } from "@/client/types.gen"
import { ConfirmDialog } from "@/components/ConfirmDialog"
import { Empty, ErrorState, ListSkeleton } from "@/components/States"
import { toaster } from "@/components/ui/toaster"
import { formatBytes, formatRelative } from "@/lib/format"
import { notifyError, notifySuccess } from "@/lib/notify"
import { invalidateOperations } from "@/lib/queryKeys"
import { downloadDocument } from "./download"
import { ACCEPTED_TYPES, validateUpload } from "./upload"

export function DocumentsTab({ tripId }: { tripId: string }) {
  const queryClient = useQueryClient()
  const input = useRef<HTMLInputElement>(null)
  const [deleting, setDeleting] = useState<DocumentRead | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)
  const query = useQuery(documentsListDocumentsOptions({ query: { trip_id: tripId } }))
  const refresh = () => invalidateOperations(queryClient, "documentsListDocuments")

  const upload = useMutation({
    ...documentsUploadDocumentMutation(),
    meta: { errorTitle: "Upload failed" },
    onSuccess: (document) => {
      notifySuccess("Uploaded", document.filename)
      return refresh()
    },
  })
  const remove = useMutation({
    ...documentsDeleteDocumentMutation(),
    meta: { errorTitle: "Couldn't delete the file" },
    onSuccess: () => refresh(),
  })

  const onFile = (file: File | undefined) => {
    if (!file) return
    const problem = validateUpload(file)
    if (problem) {
      toaster.create({ type: "error", title: "Can't upload this file", description: problem })
      return
    }
    upload.mutate({ body: { file, trip_id: tripId } })
  }

  const download = async (doc: DocumentRead) => {
    setDownloading(doc.id)
    try {
      await downloadDocument(doc.id, doc.filename)
    } catch (error) {
      notifyError(error, "Download failed")
    } finally {
      setDownloading(null)
    }
  }

  return (
    <Stack gap="4">
      <HStack justify="space-between" gap="3" flexWrap="wrap">
        <Text fontSize="sm" color="fg.muted">
          Tickets, visas and confirmations. PDF, PNG, JPEG or WebP up to 10 MB.
        </Text>
        <Button
          size="sm"
          colorPalette="brand"
          loading={upload.isPending}
          onClick={() => input.current?.click()}
        >
          <LuUpload /> Upload
        </Button>
        <Input
          ref={input}
          type="file"
          accept={ACCEPTED_TYPES.join(",")}
          display="none"
          aria-label="Choose a file to upload"
          onChange={(event) => {
            onFile(event.target.files?.[0])
            event.target.value = ""
          }}
        />
      </HStack>
      {query.isPending ? (
        <ListSkeleton rows={2} height="56px" />
      ) : query.isError ? (
        <ErrorState
          error={query.error}
          title="Couldn't load documents"
          onRetry={() => query.refetch()}
        />
      ) : query.data.length === 0 ? (
        <Empty
          icon={<LuFileText />}
          title="No documents"
          description="Keep your travel paperwork with the trip."
        />
      ) : (
        <Stack as="ul" gap="2" listStyleType="none">
          {query.data.map((doc) => (
            <HStack
              as="li"
              key={doc.id}
              gap="3"
              p="3"
              borderWidth="1px"
              borderRadius="card"
              bg="bg.panel"
            >
              <LuFileText aria-hidden="true" />
              <Stack gap="0" flex="1" minW="0">
                <Text fontWeight="500" truncate>
                  {doc.filename}
                </Text>
                <Text fontSize="xs" color="fg.muted">
                  {formatBytes(doc.size_bytes)} · {formatRelative(doc.created_at)}
                </Text>
              </Stack>
              <IconButton
                variant="ghost"
                size="sm"
                aria-label={`Download ${doc.filename}`}
                loading={downloading === doc.id}
                onClick={() => void download(doc)}
              >
                <LuDownload />
              </IconButton>
              <IconButton
                variant="ghost"
                size="sm"
                aria-label={`Delete ${doc.filename}`}
                onClick={() => setDeleting(doc)}
              >
                <LuTrash2 />
              </IconButton>
            </HStack>
          ))}
        </Stack>
      )}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Delete this file?"
        description={`“${deleting?.filename ?? ""}” will be removed permanently.`}
        confirmLabel="Delete"
        destructive
        loading={remove.isPending}
        onConfirm={() =>
          deleting &&
          remove.mutate(
            { path: { document_id: deleting.id } },
            { onSettled: () => setDeleting(null) },
          )
        }
      />
    </Stack>
  )
}
