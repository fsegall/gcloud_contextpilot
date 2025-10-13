
import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4';
import { Resend } from "npm:resend@4.0.0";
import React from 'npm:react@18.3.1';
import { renderAsync } from 'npm:@react-email/components@0.0.22';
import { InvitationEmail } from './_templates/invitation-email.tsx';

const resend = new Resend(Deno.env.get('RESEND_API_KEY') as string);
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface InviteRequest {
  workspaceId: string;
  workspaceName: string;
  email: string;
  role: 'contributor' | 'viewer';
  invitedBy: string;
}

const handler = async (req: Request): Promise<Response> => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(supabaseUrl, supabaseServiceKey);
    
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      throw new Error('No authorization header');
    }

    // Verify the user is authenticated
    const { data: { user }, error: authError } = await supabase.auth.getUser(
      authHeader.replace('Bearer ', '')
    );

    if (authError || !user) {
      throw new Error('Unauthorized');
    }

    const { workspaceId, workspaceName, email, role, invitedBy }: InviteRequest = await req.json();

    // Verify the inviter has permission to invite users
    const { data: membership } = await supabase
      .from('workspace_members')
      .select('role')
      .eq('workspace_id', workspaceId)
      .eq('user_id', invitedBy)
      .single();

    if (!membership || membership.role !== 'owner') {
      throw new Error('Insufficient permissions to invite users');
    }

    // Get inviter's profile
    const { data: inviterProfile } = await supabase
      .from('profiles')
      .select('full_name, email')
      .eq('id', invitedBy)
      .single();

    const inviterName = inviterProfile?.full_name || inviterProfile?.email || 'Someone';

    // Check if user already exists
    const { data: existingUser } = await supabase
      .from('profiles')
      .select('id')
      .eq('email', email)
      .single();

    let inviteUrl: string;

    if (existingUser) {
      // User exists, add them directly to workspace
      const { error: memberError } = await supabase
        .from('workspace_members')
        .upsert({
          workspace_id: workspaceId,
          user_id: existingUser.id,
          role,
          invited_by: invitedBy,
        });

      if (memberError) throw memberError;

      // Create invite URL to the app
      inviteUrl = `${Deno.env.get('APP_URL') || 'http://localhost:5173'}/?workspace=${workspaceId}`;
    } else {
      // User doesn't exist, create invitation link
      inviteUrl = `${Deno.env.get('APP_URL') || 'http://localhost:5173'}/auth?email=${encodeURIComponent(email)}&workspace=${workspaceId}&role=${role}`;
    }

    // Send invitation email
    const emailHtml = await renderAsync(
      React.createElement(InvitationEmail, {
        inviterName,
        workspaceName,
        role,
        inviteUrl,
      })
    );

    const { error: emailError } = await resend.emails.send({
      from: 'ContextPilot <noreply@contextpilot.dev>',
      to: [email],
      subject: `You're invited to join ${workspaceName} on ContextPilot`,
      html: emailHtml,
    });

    if (emailError) {
      console.error('Failed to send email:', emailError);
      throw new Error('Failed to send invitation email');
    }

    console.log(`Invitation sent to ${email} for workspace ${workspaceName}`);

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders,
      },
    });
  } catch (error: any) {
    console.error('Error in invite-user function:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      }
    );
  }
};

serve(handler);
